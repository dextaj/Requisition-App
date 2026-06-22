"""
requisition_api.py - Application tier for the Requisition screen.

Holds the queries the old client-side functions used to run. The "view all"
decision is enforced HERE from the caller's token, so a client asking for
scope=all without VP/Principal membership is quietly scoped back to its own
rows - exactly the guard you already had in fetch_requisitions, but now on
the server where it is the true boundary.

In production these endpoints, plus those in auth_api.py and admin_api.py,
are ONE FastAPI app - combine them with APIRouter rather than running three
separate servers. They are split per screen here only for clarity.

Run locally with:  uvicorn requisition_api:app --reload
"""

import os

import pyodbc
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from pydantic import BaseModel

app = FastAPI()

# Groups whose members may view ALL requisitions, not just their own.
VIEW_ALL_GROUPS = ("VP", "Principal")


def get_connection():
    return pyodbc.connect(os.environ["DB_CONNECTION_STRING"])


# ── Authorization ──────────────────────────────────────────────────────────
def resolve_user_id(token: str) -> int | None:
    # Placeholder: decode your signed JWT (PyJWT) or validate the Entra ID
    # token and return the user id it represents.
    raise NotImplementedError("Wire up JWT or Entra ID validation here")


def current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    user_id = resolve_user_id(auth[7:])
    if user_id is None:
        raise HTTPException(401, "Invalid token")
    return user_id


def _caller_name(cur, user_id):
    cur.execute(
        "SELECT FirstName + ' ' + LastName "
        "FROM Administration.Users WHERE UserID = ?",
        (user_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _in_any_group(cur, user_id, groups) -> bool:
    if not groups:
        return False
    placeholders = ",".join("?" * len(groups))
    cur.execute(
        "SELECT 1 FROM Administration.UserGroups ug "
        "JOIN Administration.Groups g ON g.GroupID = ug.GroupID "
        f"WHERE ug.UserID = ? AND g.GroupName IN ({placeholders})",
        (user_id, *groups),
    )
    return cur.fetchone() is not None


# ── Identity / capability ──────────────────────────────────────────────────
@app.get("/auth/me")
def me(user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        name = _caller_name(conn.cursor(), user_id)
    return {"user_id": user_id, "full_name": name or ""}


@app.get("/auth/in-any-group")
def in_any_group(group: list[str] = Query(default=[]),
                 user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        return {"in_any": _in_any_group(conn.cursor(), user_id, group)}


# ── Requisitions ───────────────────────────────────────────────────────────
@app.get("/requisitions")
def list_requisitions(scope: str = "mine",
                      user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, user_id)
        # scope=all is honored ONLY for VP/Principal; otherwise scoped to own.
        view_all = scope == "all" and _in_any_group(cur, user_id, VIEW_ALL_GROUPS)
        if view_all:
            cur.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE")
        else:
            cur.execute(
                "SELECT * FROM REQUISITION.REQUISITION_TABLE WHERE Assign_To = ?",
                (name,),
            )
        # Rows are returned as JSON arrays in column order, so the UI's
        # positional indexing (row[2], row[10], row[15]...) still works.
        # FastAPI serializes dates/decimals to strings/numbers automatically.
        return [list(r) for r in cur.fetchall()]


@app.get("/requisitions/summary")
def summary(user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, user_id)

        cur.execute(
            "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
            "WHERE Assign_To = ? AND Phase != 'Accounts'", (name,))
        my_open = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
            "WHERE Assign_To = ? AND Phase = 'Draft'", (name,))
        pending = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
            "WHERE MONTH(Submit_Date) = MONTH(GETDATE()) "
            "AND YEAR(Submit_Date) = YEAR(GETDATE())")
        total_month = cur.fetchone()[0]

    return {"my_open": my_open, "pending": pending, "total_month": total_month}


# ── Session hand-off (transitional - retire with RequisitionForm) ──────────
class SessionIn(BaseModel):
    os_user: str


@app.post("/session")
def register_session(body: SessionIn, user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, user_id)
        cur.execute("SELECT Logon_ID FROM Administration.LogOnUser WHERE OSuser = ?",
                    (body.os_user,))
        if cur.fetchone():
            cur.execute(
                "UPDATE Administration.LogOnUser "
                "SET UserID=?, UserName=?, DocNumber=NULL WHERE OSuser=?",
                (user_id, name, body.os_user))
        else:
            cur.execute(
                "INSERT INTO Administration.LogOnUser "
                "(UserID, UserName, OSuser, DocNumber) VALUES (?, ?, ?, NULL)",
                (user_id, name, body.os_user))
        conn.commit()
    return {"ok": True}


class DocOpenIn(BaseModel):
    os_user: str
    doc_number: str


@app.put("/session/document")
def log_document_open(body: DocOpenIn, user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE Administration.LogOnUser SET DocNumber = ? WHERE OSuser = ?",
            (body.doc_number, body.os_user))
        conn.commit()
    return {"ok": True}
