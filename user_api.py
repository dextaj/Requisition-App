"""
user_api.py - Application tier for the User management screen.

The highest-privilege endpoints in the system: creating accounts and setting
passwords. Every one is gated by require_admin, so only Administration members
can manage users - enforced server-side, not by hiding a button.

Passwords are hashed HERE with bcrypt. The client sends the plaintext over
HTTPS and never computes the stored hash. The login endpoint already verifies
bcrypt-or-SHA-256, so existing SHA-256 accounts keep working and new ones get
bcrypt.

In production this joins auth_api / admin_api / requisition_api /
requisition_form_api under one APIRouter. When merged, this user-management
resource is the canonical /users (it carries OSuser); the lighter user lists
the other screens use are the same resource, projected to fewer fields.

Run locally with:  uvicorn user_api:app --reload
"""

import os

import bcrypt
import pyodbc
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

ADMIN_GROUP = "Administration"


def get_connection():
    return pyodbc.connect(os.environ["DB_CONNECTION_STRING"])


# ── Authorization ──────────────────────────────────────────────────────────
def resolve_user_id(token: str) -> int | None:
    raise NotImplementedError("Wire up JWT or Entra ID validation here")


def current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    uid = resolve_user_id(auth[7:])
    if uid is None:
        raise HTTPException(401, "Invalid token")
    return uid


def require_admin(user_id: int = Depends(current_user_id)) -> int:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM Administration.UserGroups ug "
                "JOIN Administration.Groups g ON g.GroupID = ug.GroupID "
                "WHERE ug.UserID = ? AND g.GroupName = ?", (user_id, ADMIN_GROUP))
            if cur.fetchone() is None:
                raise HTTPException(403, "Not a member of the Administration group.")
    except pyodbc.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return user_id


# ── Payload ────────────────────────────────────────────────────────────────
class UserIn(BaseModel):
    first: str
    last: str
    email: str
    username: str
    osuser: str | None = None
    password: str | None = None     # required on create; blank on update keeps existing


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Reads ──────────────────────────────────────────────────────────────────
@app.get("/users")
def list_users(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT UserID, FirstName, LastName, UserName, Email, OSuser "
            "FROM Administration.Users ORDER BY LastName, FirstName")
        # Positional arrays so the screen's row[0]..row[5] indexing still works.
        return [list(r) for r in cur.fetchall()]


@app.get("/users/{user_id}")
def get_user(user_id: int, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT UserID, FirstName, LastName, UserName, Email, OSuser "
            "FROM Administration.Users WHERE UserID = ?", (user_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "User not found")
    return list(row)


# ── Writes ─────────────────────────────────────────────────────────────────
@app.post("/users")
def create_user(body: UserIn, _: int = Depends(require_admin)):
    if not body.password:
        raise HTTPException(400, "Password is required for new users.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Administration.Users "
            "(FirstName, LastName, Email, UserName, Password_hash, OSuser) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (body.first, body.last, body.email, body.username,
             _hash(body.password), body.osuser or None))
        conn.commit()
    return {"ok": True}


@app.put("/users/{user_id}")
def update_user(user_id: int, body: UserIn, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        if body.password:
            cur.execute(
                "UPDATE Administration.Users SET "
                "FirstName=?, LastName=?, Email=?, UserName=?, "
                "Password_hash=?, OSuser=? WHERE UserID=?",
                (body.first, body.last, body.email, body.username,
                 _hash(body.password), body.osuser or None, user_id))
        else:
            cur.execute(
                "UPDATE Administration.Users SET "
                "FirstName=?, LastName=?, Email=?, UserName=?, OSuser=? "
                "WHERE UserID=?",
                (body.first, body.last, body.email, body.username,
                 body.osuser or None, user_id))
        conn.commit()
    return {"ok": True}
