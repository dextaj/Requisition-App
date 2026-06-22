"""
admin_api.py - Application tier for the Admin console (Azure App Service).

Holds every query the old client-side Database class used to run, now behind
HTTPS endpoints. Two differences from the desktop version that matter:

  1. The DB connection string lives in server config (App Service settings or
     Key Vault) and is read from the environment - never on a client.
  2. Authorization is enforced HERE, on every request, from the caller's
     token - not from a user id passed on a command line that anyone could
     fake. require_admin() gates all of these endpoints at once.

Run locally with:  uvicorn admin_api:app --reload
"""

import os
import base64

import pyodbc
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from pydantic import BaseModel

app = FastAPI()

ADMIN_GROUP = "Administration"
CORE_GROUPS = ("Administration", "HOD", "VP", "Principal")


def get_connection():
    return pyodbc.connect(os.environ["DB_CONNECTION_STRING"])


# ── Authorization ──────────────────────────────────────────────────────────
def resolve_user_id(token: str) -> int | None:
    # Placeholder: decode your signed JWT (e.g. PyJWT) or validate the
    # Microsoft Entra ID token, and return the user id it represents.
    raise NotImplementedError("Wire up JWT or Entra ID validation here")


def current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    user_id = resolve_user_id(auth[7:])
    if user_id is None:
        raise HTTPException(401, "Invalid token")
    return user_id


def _in_group(cur, user_id, group_name) -> bool:
    cur.execute(
        "SELECT 1 FROM Administration.UserGroups ug "
        "JOIN Administration.Groups g ON g.GroupID = ug.GroupID "
        "WHERE ug.UserID = ? AND g.GroupName = ?",
        (user_id, group_name),
    )
    return cur.fetchone() is not None


def require_admin(user_id: int = Depends(current_user_id)) -> int:
    """Every admin endpoint depends on this. Fails closed on DB error."""
    try:
        with get_connection() as conn:
            if not _in_group(conn.cursor(), user_id, ADMIN_GROUP):
                raise HTTPException(403, "Not a member of the Administration group.")
    except pyodbc.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return user_id


def _require_keyword_table(cur, table: str) -> None:
    cur.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = 'Keywords' AND TABLE_TYPE = 'BASE TABLE'"
    )
    if table not in {r[0] for r in cur.fetchall()}:
        raise HTTPException(404, f"Unknown keyword table: {table}")


# ── Identity ─────────────────────────────────────────────────────────────--
@app.get("/auth/me")
def me(user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT FirstName, LastName FROM Administration.Users WHERE UserID = ?",
                    (user_id,))
        row = cur.fetchone()
        is_admin = _in_group(cur, user_id, ADMIN_GROUP)
    return {
        "user_id": user_id,
        "full_name": f"{row[0]} {row[1]}" if row else "",
        "is_admin": is_admin,
    }


# ── Users ────────────────────────────────────────────────────────────────--
@app.get("/users")
def list_users(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT UserID, FirstName, LastName, UserName, Email "
                    "FROM Administration.Users")
        return [list(r) for r in cur.fetchall()]


@app.get("/users/{user_id}/in-group")
def user_in_group(user_id: int, group: str = Query(...), _: int = Depends(require_admin)):
    with get_connection() as conn:
        return {"in_group": _in_group(conn.cursor(), user_id, group)}


# ── Keyword tables ─────────────────────────────────────────────────────────
@app.get("/keywords/tables")
def keyword_tables(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'Keywords' AND TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_NAME"
        )
        return [r[0] for r in cur.fetchall()]


@app.get("/keywords/{table}")
def keyword_rows(table: str, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        _require_keyword_table(cur, table)
        cur.execute(f"SELECT Id, keywordName, isActive FROM Keywords.[{table}]")
        return [list(r) for r in cur.fetchall()]


class KeywordChangesIn(BaseModel):
    updated:  list[tuple[int, str, bool]]
    deleted:  list[int]
    inserted: list[tuple[str, bool]]


@app.put("/keywords/{table}")
def save_keywords(table: str, changes: KeywordChangesIn, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        _require_keyword_table(cur, table)
        tbl = f"Keywords.[{table}]"
        for row_id in changes.deleted:
            cur.execute(f"DELETE FROM {tbl} WHERE Id = ?", (row_id,))
        for row_id, name, active in changes.updated:
            cur.execute(f"UPDATE {tbl} SET keywordName = ?, isActive = ? WHERE Id = ?",
                        (name, 1 if active else 0, row_id))
        for name, active in changes.inserted:
            cur.execute(f"INSERT INTO {tbl} (keywordName, isActive) VALUES (?, ?)",
                        (name, 1 if active else 0))
        conn.commit()
    return {"ok": True}


# ── Groups ───────────────────────────────────────────────────────────────--
@app.post("/groups/ensure-core")
def ensure_core_groups(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        for name in CORE_GROUPS:
            cur.execute(
                "IF NOT EXISTS "
                "(SELECT 1 FROM Administration.Groups WHERE GroupName = ?) "
                "INSERT INTO Administration.Groups (GroupName) VALUES (?)",
                (name, name),
            )
        conn.commit()
    return {"ok": True}


@app.get("/groups")
def fetch_groups(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT g.GroupID, g.GroupName, COUNT(ug.UserID) "
            "FROM Administration.Groups g "
            "LEFT JOIN Administration.UserGroups ug ON ug.GroupID = g.GroupID "
            "GROUP BY g.GroupID, g.GroupName ORDER BY g.GroupName"
        )
        return [list(r) for r in cur.fetchall()]


class GroupIn(BaseModel):
    name: str


@app.post("/groups")
def create_group(body: GroupIn, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Administration.Groups (GroupName) VALUES (?)",
                    (body.name,))
        conn.commit()
    return {"ok": True}


@app.get("/groups/{group_id}/members")
def group_member_ids(group_id: int, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT UserID FROM Administration.UserGroups WHERE GroupID = ?",
                    (group_id,))
        return [r[0] for r in cur.fetchall()]


class MembershipIn(BaseModel):
    add:    list[int]
    remove: list[int]


@app.put("/groups/{group_id}/members")
def set_group_membership(group_id: int, body: MembershipIn, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        for uid in body.remove:
            cur.execute("DELETE FROM Administration.UserGroups "
                        "WHERE GroupID = ? AND UserID = ?", (group_id, uid))
        for uid in body.add:
            cur.execute(
                "IF NOT EXISTS (SELECT 1 FROM Administration.UserGroups "
                "WHERE GroupID = ? AND UserID = ?) "
                "INSERT INTO Administration.UserGroups (GroupID, UserID) VALUES (?, ?)",
                (group_id, uid, group_id, uid),
            )
        conn.commit()
    return {"ok": True}


# ── Signatures (base64 in / out) ───────────────────────────────────────────
@app.get("/users/{user_id}/signature")
def get_signature(user_id: int, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SignatureData, ContentType "
                    "FROM Administration.UserSignatures WHERE UserID = ?", (user_id,))
        row = cur.fetchone()
    if row is None or row[0] is None:
        return {"data": None, "content_type": None}
    return {"data": base64.b64encode(bytes(row[0])).decode("ascii"),
            "content_type": row[1]}


class SignatureIn(BaseModel):
    data: str            # base64-encoded image bytes
    content_type: str


@app.put("/users/{user_id}/signature")
def save_signature(user_id: int, body: SignatureIn, caller: int = Depends(require_admin)):
    blob = pyodbc.Binary(base64.b64decode(body.data))
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE Administration.UserSignatures "
            "SET SignatureData = ?, ContentType = ?, "
            "UpdatedDate = SYSUTCDATETIME(), UpdatedBy = ? WHERE UserID = ?",
            (blob, body.content_type, caller, user_id),   # updated_by = the token's user
        )
        if cur.rowcount == 0:
            cur.execute(
                "INSERT INTO Administration.UserSignatures "
                "(UserID, SignatureData, ContentType, UpdatedBy) VALUES (?, ?, ?, ?)",
                (user_id, blob, body.content_type, caller),
            )
        conn.commit()
    return {"ok": True}


@app.delete("/users/{user_id}/signature")
def delete_signature(user_id: int, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Administration.UserSignatures WHERE UserID = ?",
                    (user_id,))
        conn.commit()
    return {"ok": True}
