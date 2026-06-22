"""
user_db.py - client data layer for the User screen (local dev).

Admin-only on the server side. The token comes from CTC_AUTH_TOKEN, which must
be an Administration member's token. During isolated testing you set that in
the terminal; once the admin screen is converted it will pass it automatically.
"""

import os

import requests
import applog

log = applog.get_logger("user")

_BASE = os.environ.get("CTC_API_BASE", "http://localhost:8000").rstrip("/")
_session = requests.Session()
_token = os.environ.get("CTC_AUTH_TOKEN")
if _token:
    _session.headers["Authorization"] = f"Bearer {_token}"


def _get(path, **kw):
    r = _session.get(_BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def _send(method, path, **kw):
    r = _session.request(method, _BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json() if r.content else None


def fetch_all_users():
    # [UserID, FirstName, LastName, UserName, Email, OSuser] per row.
    try:
        return _get("/users")
    except requests.RequestException as exc:
        log.error("fetch_all_users failed: %s", exc)
        return []


def fetch_user(user_id):
    return _get(f"/users/{user_id}")


def save_user(user_id, first, last, email, username, osuser, password=None):
    payload = {
        "first": first, "last": last, "email": email, "username": username,
        "osuser": osuser or None, "password": password or None,
    }
    if user_id is None:
        _send("POST", "/users", json=payload)
    else:
        _send("PUT", f"/users/{user_id}", json=payload)
