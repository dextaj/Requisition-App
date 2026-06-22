"""
admin_db.py - client data layer for the Admin console (local dev).

Same method names and return shapes as the old pyodbc Database class, so the
KeywordWindow / GroupWindow / SignatureWindow / AdminScreen UI is unchanged.
Each call now goes to the API. Token comes from CTC_AUTH_TOKEN, or in dev from
the UserID the login screen passes on the command line.
"""

import os
import sys
import base64
from dataclasses import dataclass

import requests
import applog

log = applog.get_logger("admin")

_BASE = os.environ.get("CTC_API_BASE", "http://localhost:8000").rstrip("/")
_session = requests.Session()
_token = os.environ.get("CTC_AUTH_TOKEN")
if not _token and len(sys.argv) > 1 and sys.argv[1].strip().isdigit():
    _token = f"dev:{sys.argv[1].strip()}"
if _token:
    _session.headers["Authorization"] = f"Bearer {_token}"


def token():
    return _token


@dataclass
class KeywordChanges:
    updated: list
    deleted: list
    inserted: list


def _get(path, **kw):
    r = _session.get(_BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def _send(method, path, **kw):
    r = _session.request(method, _BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json() if r.content else None


class Database:
    CORE_GROUPS = ("Administration", "HOD", "VP", "Principal")

    def __init__(self, conn_string=None):
        pass  # no database connection on the client anymore

    # ── Users ──
    def fetch_users(self):
        try:
            return _get("/users")
        except requests.RequestException as exc:
            log.error("fetch_users failed: %s", exc)
            return []

    # ── Keyword tables ──
    def keyword_tables(self, refresh=False):
        try:
            return _get("/keywords/tables")
        except requests.RequestException as exc:
            log.error("keyword_tables failed: %s", exc)
            return []

    def keyword_rows(self, table):
        try:
            return _get(f"/keywords/{table}")
        except requests.RequestException as exc:
            log.error("keyword_rows failed: %s", exc)
            return []

    def save_keywords(self, table, changes):
        _send("PUT", f"/keywords/{table}", json={
            "updated": [list(u) for u in changes.updated],
            "deleted": list(changes.deleted),
            "inserted": [list(i) for i in changes.inserted]})

    # ── Groups ──
    def ensure_core_groups(self):
        try:
            _send("POST", "/groups/ensure-core")
        except requests.RequestException as exc:
            log.error("ensure_core_groups failed: %s", exc)

    def fetch_groups(self):
        try:
            return _get("/groups")
        except requests.RequestException as exc:
            log.error("fetch_groups failed: %s", exc)
            return []

    def create_group(self, name):
        _send("POST", "/groups", json={"name": name})

    def fetch_group_member_ids(self, group_id):
        try:
            return set(_get(f"/groups/{group_id}/members"))
        except requests.RequestException as exc:
            log.error("fetch_group_member_ids failed: %s", exc)
            return set()

    def set_group_membership(self, group_id, to_add, to_remove):
        _send("PUT", f"/groups/{group_id}/members",
              json={"add": list(to_add), "remove": list(to_remove)})

    def user_in_group(self, user_id, group_name):
        try:
            return _get("/auth/in-any-group",
                        params=[("group", group_name)])["in_any"]
        except requests.RequestException as exc:
            log.error("user_in_group failed: %s", exc)
            return False

    # ── Signatures ──
    def fetch_signature(self, user_id):
        try:
            data = _get(f"/users/{user_id}/signature")
        except requests.RequestException as exc:
            log.error("fetch_signature failed: %s", exc)
            return None, None
        if not data or data.get("data") is None:
            return None, None
        return base64.b64decode(data["data"]), data["content_type"]

    def save_signature(self, user_id, data, content_type, updated_by=None):
        # updated_by is ignored; the server records the token's user.
        _send("PUT", f"/users/{user_id}/signature",
              json={"data": base64.b64encode(data).decode("ascii"),
                    "content_type": content_type})

    def delete_signature(self, user_id):
        _send("DELETE", f"/users/{user_id}/signature")
