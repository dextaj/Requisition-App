"""
auth_api.py - Application tier (LOCAL DEV BUILD).

One server for everything so far: the login endpoint, plus the requisition
list endpoints. Runs against your existing SQL Server. Same command as before:

    set CTC_DEV_AUTH=1
    uvicorn auth_api:app --reload
"""
# deploy test
import os
import hashlib

import bcrypt
import pyodbc
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from pydantic import BaseModel

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_GROUP = "Administration"
VIEW_ALL_GROUPS = ("VP", "Principal")

LOCAL_CONN = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=Chris;"
    "Database=ChurchTeachersCollegeDB;"
    "Trusted_Connection=yes;"
    "Encrypt=Optional;"
)


# DEV ONLY - token format "dev:<user_id>", gated by an env flag so it can't ship.
# Resolves an auth token to a user id, or None to reject (-> 401).
# Real path: verify a signed JWT. Dev path: accept "dev:<id>" only when CTC_DEV_AUTH=1.
def resolve_user_id(token: str) -> int | None:
    # Dev shortcut — only when explicitly enabled, never in production.
    if os.environ.get("CTC_DEV_AUTH") == "1" and token.startswith("dev:"):
        try:
            return int(token.split(":", 1)[1])
        except ValueError:
            return None

    # Real path: a signed JWT issued by /auth/login.
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None

def get_connection():
    return pyodbc.connect(os.environ.get("DB_CONNECTION_STRING", LOCAL_CONN))


# Reads the bearer token and turns it into the caller's user id.
def current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    uid = resolve_user_id(auth[7:])
    if uid is None:
        raise HTTPException(401, "Invalid token")
    return uid


def _caller_name(cur, user_id):
    cur.execute("SELECT FirstName + ' ' + LastName "
                "FROM Administration.Users WHERE UserID = ?", (user_id,))
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
        (user_id, *groups))
    return cur.fetchone() is not None


# ── Login ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str
    os_user: str | None = None


class LoginResponse(BaseModel):
    user_id: int
    full_name: str
    is_admin: bool
    token: str


def verify_password(plain: str, stored_hash) -> bool:
    plain = (plain or "").strip()
    stored_s = stored_hash.strip() if isinstance(stored_hash, str) else stored_hash
    try:
        stored_bytes = stored_hash.encode() if isinstance(stored_hash, str) else stored_hash
        if bcrypt.checkpw(plain.encode(), stored_bytes):
            return True
    except (ValueError, TypeError):
        pass
    if isinstance(stored_s, str) and \
            hashlib.sha256(plain.encode()).hexdigest() == stored_s:
        return True
    # DEV ONLY: accept legacy plain-text passwords during local testing.
    if os.environ.get("CTC_DEV_AUTH") == "1" and isinstance(stored_s, str) \
            and plain == stored_s:
        return True
    return False


def register_logon(cursor, user_id, user_name, os_user):
    cursor.execute("SELECT Logon_ID FROM Administration.LogOnUser WHERE OSuser = ?",
                   (os_user,))
    if cursor.fetchone():
        cursor.execute("UPDATE Administration.LogOnUser "
                       "SET UserID=?, UserName=?, DocNumber=NULL WHERE OSuser=?",
                       (user_id, user_name, os_user))
    else:
        cursor.execute("INSERT INTO Administration.LogOnUser "
                       "(UserID, UserName, OSuser, DocNumber) VALUES (?, ?, ?, NULL)",
                       (user_id, user_name, os_user))


def issue_token(user_id: int, is_admin: bool) -> str:
    # Real signed JWT (was the dev:<id> string). is_admin is intentionally not
    # encoded — the server re-checks group membership per request, so the token
    # only proves identity, not privileges.
    return create_token(user_id)

@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT UserID, FirstName, LastName, Password_hash "
                        "FROM Administration.Users WHERE UserName = ?", (req.username,))
            row = cur.fetchone()
            if row is None or not verify_password(req.password, row.Password_hash):
                raise HTTPException(status_code=401, detail="Incorrect username or password.")
            user_id, first, last, _ = row
            full_name = f"{first} {last}"
            cur.execute("SELECT 1 FROM Administration.UserGroups ug "
                        "JOIN Administration.Groups g ON g.GroupID = ug.GroupID "
                        "WHERE ug.UserID = ? AND g.GroupName = ?", (user_id, ADMIN_GROUP))
            is_admin = cur.fetchone() is not None
            if req.os_user:
                register_logon(cur, user_id, full_name, req.os_user)
            conn.commit()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return LoginResponse(user_id=user_id, full_name=full_name,
                         is_admin=is_admin, token=issue_token(user_id, is_admin))


# ── Requisition list ───────────────────────────────────────────────────────
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


@app.get("/requisitions")
def list_requisitions(scope: str = "mine", user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, user_id)
        view_all = scope == "all" and _in_any_group(cur, user_id, VIEW_ALL_GROUPS)
        if view_all:
            cur.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE")
        else:
            cur.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE WHERE Assign_To = ?",
                        (name,))
        return [list(r) for r in cur.fetchall()]
       
@app.get("/requisitions/summary")
def summary(user_id: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, user_id)
        cur.execute("SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Assign_To = ? AND Phase != 'Accounts'", (name,))
        my_open = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Assign_To = ? AND Phase = 'Draft'", (name,))
        pending = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE MONTH(Submit_Date) = MONTH(GETDATE()) "
                    "AND YEAR(Submit_Date) = YEAR(GETDATE())")
        total_month = cur.fetchone()[0]
    return {"my_open": my_open, "pending": pending, "total_month": total_month}


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
            cur.execute("UPDATE Administration.LogOnUser "
                        "SET UserID=?, UserName=?, DocNumber=NULL WHERE OSuser=?",
                        (user_id, name, body.os_user))
        else:
            cur.execute("INSERT INTO Administration.LogOnUser "
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
        cur.execute("UPDATE Administration.LogOnUser SET DocNumber = ? WHERE OSuser = ?",
                    (body.doc_number, body.os_user))
        conn.commit()
    return {"ok": True}
    
# ── User management (admin-only) ───────────────────────────────────────────
def require_admin(user_id: int = Depends(current_user_id)) -> int:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM Administration.UserGroups ug "
                        "JOIN Administration.Groups g ON g.GroupID = ug.GroupID "
                        "WHERE ug.UserID = ? AND g.GroupName = ?", (user_id, ADMIN_GROUP))
            if cur.fetchone() is None:
                raise HTTPException(403, "Not a member of the Administration group.")
    except pyodbc.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return user_id


class UserIn(BaseModel):
    first: str
    last: str
    email: str
    username: str
    osuser: str | None = None
    password: str | None = None


@app.get("/users")
def list_users(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT UserID, FirstName, LastName, UserName, Email, OSuser "
                    "FROM Administration.Users ORDER BY LastName, FirstName")
        return [list(r) for r in cur.fetchall()]


@app.get("/users/{user_id}")
def get_user(user_id: int, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT UserID, FirstName, LastName, UserName, Email, OSuser "
                    "FROM Administration.Users WHERE UserID = ?", (user_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "User not found")
    return list(row)


@app.post("/users")
def create_user(body: UserIn, _: int = Depends(require_admin)):
    if not body.password:
        raise HTTPException(400, "Password is required for new users.")
    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Administration.Users "
                    "(FirstName, LastName, Email, UserName, Password_hash, OSuser) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (body.first, body.last, body.email, body.username,
                     pw_hash, body.osuser or None))
        conn.commit()
    return {"ok": True}


@app.put("/users/{user_id}")
def update_user(user_id: int, body: UserIn, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        if body.password:
            pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
            cur.execute("UPDATE Administration.Users SET "
                        "FirstName=?, LastName=?, Email=?, UserName=?, "
                        "Password_hash=?, OSuser=? WHERE UserID=?",
                        (body.first, body.last, body.email, body.username,
                         pw_hash, body.osuser or None, user_id))
        else:
            cur.execute("UPDATE Administration.Users SET "
                        "FirstName=?, LastName=?, Email=?, UserName=?, OSuser=? "
                        "WHERE UserID=?",
                        (body.first, body.last, body.email, body.username,
                         body.osuser or None, user_id))
        conn.commit()
    return {"ok": True}
    
import base64
CORE_GROUPS = ("Administration", "HOD", "VP", "Principal")


# ── Admin: keyword tables ──────────────────────────────────────────────────
def _require_keyword_table(cur, table):
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = 'Keywords' AND TABLE_TYPE = 'BASE TABLE'")
    if table not in {r[0] for r in cur.fetchall()}:
        raise HTTPException(404, f"Unknown keyword table: {table}")


@app.get("/keywords/tables")
def keyword_tables(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA = 'Keywords' AND TABLE_TYPE = 'BASE TABLE' "
                    "ORDER BY TABLE_NAME")
        return [r[0] for r in cur.fetchall()]


@app.get("/keywords/{table}")
def keyword_rows(table: str, _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        _require_keyword_table(cur, table)
        cur.execute(f"SELECT Id, keywordName, isActive FROM Keywords.[{table}]")
        return [list(r) for r in cur.fetchall()]


class KeywordChangesIn(BaseModel):
    updated: list[tuple[int, str, bool]]
    deleted: list[int]
    inserted: list[tuple[str, bool]]


@app.put("/keywords/{table}")
def save_keywords(table: str, changes: KeywordChangesIn,
                  _: int = Depends(require_admin)):
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


# ── Admin: groups ──────────────────────────────────────────────────────────
@app.post("/groups/ensure-core")
def ensure_core_groups(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        for name in CORE_GROUPS:
            cur.execute("IF NOT EXISTS "
                        "(SELECT 1 FROM Administration.Groups WHERE GroupName = ?) "
                        "INSERT INTO Administration.Groups (GroupName) VALUES (?)",
                        (name, name))
        conn.commit()
    return {"ok": True}


@app.get("/groups")
def fetch_groups(_: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT g.GroupID, g.GroupName, COUNT(ug.UserID) "
                    "FROM Administration.Groups g "
                    "LEFT JOIN Administration.UserGroups ug ON ug.GroupID = g.GroupID "
                    "GROUP BY g.GroupID, g.GroupName ORDER BY g.GroupName")
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
    add: list[int]
    remove: list[int]


@app.put("/groups/{group_id}/members")
def set_group_membership(group_id: int, body: MembershipIn,
                         _: int = Depends(require_admin)):
    with get_connection() as conn:
        cur = conn.cursor()
        for uid in body.remove:
            cur.execute("DELETE FROM Administration.UserGroups "
                        "WHERE GroupID = ? AND UserID = ?", (group_id, uid))
        for uid in body.add:
            cur.execute("IF NOT EXISTS (SELECT 1 FROM Administration.UserGroups "
                        "WHERE GroupID = ? AND UserID = ?) "
                        "INSERT INTO Administration.UserGroups (GroupID, UserID) "
                        "VALUES (?, ?)", (group_id, uid, group_id, uid))
        conn.commit()
    return {"ok": True}


# ── Admin: signatures ──────────────────────────────────────────────────────
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
    data: str
    content_type: str


@app.put("/users/{user_id}/signature")
def save_signature(user_id: int, body: SignatureIn,
                   caller: int = Depends(require_admin)):
    blob = pyodbc.Binary(base64.b64decode(body.data))
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Administration.UserSignatures "
                    "SET SignatureData = ?, ContentType = ?, "
                    "UpdatedDate = SYSUTCDATETIME(), UpdatedBy = ? WHERE UserID = ?",
                    (blob, body.content_type, caller, user_id))
        if cur.rowcount == 0:
            cur.execute("INSERT INTO Administration.UserSignatures "
                        "(UserID, SignatureData, ContentType, UpdatedBy) "
                        "VALUES (?, ?, ?, ?)", (user_id, blob, body.content_type, caller))
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

import re
import uuid
import shutil
from datetime import date
from fastapi import UploadFile, File
from fastapi.responses import FileResponse

STORAGE_DIR = os.environ.get(
    "CTC_ATTACH_DIR", os.path.join(os.path.expanduser("~"), "CTC_Attachments"))

DOC_PREFIXES = {"Transport": "TRAN-", "Infrastructure": "INFR-",
                "Household": "HSLD-", "Kitchen": "KTCN-"}
PHASES_STANDARD    = ["Draft", "HOD Review", "VP Review",
                      "Principal Approval", "Procurement", "Accounts", "Completed"]
PHASES_MAINTENANCE = ["Draft", "HOD Review", "VP Review", "Maintenance Unit",
                      "VP Approval", "Principal Approval", "Procurement", "Accounts", "Completed"]
PHASES_TRANSPORT   = ["Draft", "HOD Review", "VP Approval", "Accounts", "Completed"]
APPROVER_PHASE_COLUMN = {
    "HOD Review": "HOD_Approver_ID", "VP Review": "VP_Approver_ID",
    "VP Approval": "VP_Approver_ID", "Principal Approval": "Principal_Approver_ID"}


def _form_phases(category, via_maintenance=False):
    if category == "Transport":
        return PHASES_TRANSPORT
    return PHASES_MAINTENANCE if via_maintenance else PHASES_STANDARD


class ReqFields(BaseModel):
    Site: str = ""; Category: str = ""; Maintenance: str = ""
    Department: str = ""; Academic: str = ""; Supplier: str = ""
    Purpose: str = ""; Requesting: str = ""; HOD_Comment: str = ""
    VP_Comment: str = ""; Request_Type: str = ""; Scope: str = ""
    Contractor: str = ""; Material: str = ""; VP_Approval: str = ""
    Principal_Comment: str = ""; Maintenance_Unit: int = 0
    Trip_Date: str = ""; Destination: str = ""; Departure_Time: str = ""
    Cost: str = ""; VP_Signature: str = ""; Principal_Signature: str = ""
    Accounts_Acknowledged: int = 0
    Send_Kitchen: int = 0; Send_Household: int = 0
    Send_IT: int = 0; Send_Maintenance: int = 0
    Processed_Refs: str = ""

class ReqItem(BaseModel):
    Item_Name: str = ""; Amt_In_Stock: str = ""; Quantity_Requested: str = ""
    Comments: str = ""; Broiler: int = 0; Layer: int = 0
    Pigs: int = 0; Gen_Supply: int = 0


class SaveReqIn(BaseModel):
    fields: ReqFields
    items: list[ReqItem] = []


class SubmitReqIn(BaseModel):
    fields: ReqFields
    items: list[ReqItem] = []
    assignee: str = ""
    completed_phase: str = ""
    comments: str = ""
    next_phase: str = ""
    
_REQ_SET = ("Site=?,Category=?,Maintenance=?,Department=?,Academic=?,Supplier=?,"
            "Purpose=?,Requesting=?,HOD_Comment=?,VP_Comment=?,Request_Type=?,Scope=?,"
            "Contractor=?,Material=?,VP_Approval=?,Principal_Comment=?,Maintenance_Unit=?,"
            "Trip_Date=?,Destination=?,Departure_Time=?,Cost=?,VP_Signature=?,"
            "Principal_Signature=?,Accounts_Acknowledged=?,"
            "Send_Kitchen=?,Send_Household=?,Send_IT=?,Send_Maintenance=?,Processed_Refs=?")


def _req_params(f):
    return (f.Site, f.Category, f.Maintenance, f.Department, f.Academic, f.Supplier,
            f.Purpose, f.Requesting, f.HOD_Comment, f.VP_Comment, f.Request_Type, f.Scope,
            f.Contractor, f.Material, f.VP_Approval, f.Principal_Comment, f.Maintenance_Unit,
            f.Trip_Date, f.Destination, f.Departure_Time, f.Cost, f.VP_Signature,
            f.Principal_Signature, f.Accounts_Acknowledged,
            f.Send_Kitchen, f.Send_Household, f.Send_IT, f.Send_Maintenance,
            f.Processed_Refs)

def _req_log_history(cur, doc, phase, action, action_by, assigned_to="", comments=""):
    cur.execute("INSERT INTO REQUISITION.REQUISITION_HISTORY "
                "(Document_Number, Phase, Action, Action_Date, Action_By, "
                "Assigned_To, Comments) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (doc, phase, action, date.today().isoformat(),
                 action_by, assigned_to, comments))


def _req_sync_items(cur, doc, items):
    cur.execute("DELETE FROM REQUISITION.REQUISITION_ITEMS WHERE Document_Number = ?", (doc,))
    for d in items:
        cur.execute("INSERT INTO REQUISITION.REQUISITION_ITEMS "
                    "(Document_Number, Item_Name, Amt_In_Stock, Quantity_Requested, "
                    "Comments, Broiler, Layer, Pigs, Gen_Supply) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (doc, d.Item_Name, d.Amt_In_Stock, d.Quantity_Requested, d.Comments,
                     d.Broiler, d.Layer, d.Pigs, d.Gen_Supply))


@app.get("/lists")
def req_lists(_: int = Depends(current_user_id)):
    out = {}
    with get_connection() as conn:
        cur = conn.cursor()
        for key, table in (("site", "Site"), ("category", "Category"),
                           ("maintenance", "Maintenance"), ("department", "Department"),
                           ("academic", "Academic")):
            cur.execute(f"SELECT KeywordName FROM Keywords.{table} "
                        f"WHERE isActive = 0 ORDER BY KeywordName")  # mirrors original
            out[key] = [r[0] for r in cur.fetchall()]
    return out


@app.get("/user-names")
def req_user_names(_: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT FirstName, LastName FROM Administration.Users")
        return [f"{r[0]} {r[1]}" for r in cur.fetchall()]


@app.get("/doc-number")
def req_doc_number(category: str = "", _: int = Depends(current_user_id)):
    prefix = DOC_PREFIXES.get(category, "OFFS-") if category else ""
    if not prefix:
        return {"doc_number": ""}
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(Document_Number) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number LIKE ?", (f"%{prefix}%",))
        row = cur.fetchone()
        counter = 0
        if row and row[0]:
            nums = re.findall(r"\d+", row[0]); counter = int(nums[-1]) if nums else 0
    return {"doc_number": f"{prefix}{counter + 1:05d}"}


@app.get("/session")
def req_session(os_user: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DocNumber FROM Administration.LogOnUser WHERE OSuser = ?",
                    (os_user,))
        row = cur.fetchone()
    return {"doc_number": (row[0] if row else None)}


@app.get("/requisitions/{doc}")
def req_get(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?",
                    (doc,))
        row = cur.fetchone()
        if row is None:
            return None
        return {d[0]: v for d, v in zip(cur.description, row)}


@app.get("/requisitions/{doc}/items")
def req_items(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Item_Name, Amt_In_Stock, Quantity_Requested, Comments, "
                    "Broiler, Layer, Pigs, Gen_Supply FROM REQUISITION.REQUISITION_ITEMS "
                    "WHERE Document_Number = ? ORDER BY Item_ID ASC", (doc,))
        return [{"Item_Name": r[0] or "", "Amt_In_Stock": r[1] or "",
                 "Quantity_Requested": r[2] or "", "Comments": r[3] or "",
                 "Broiler": bool(r[4]), "Layer": bool(r[5]),
                 "Pigs": bool(r[6]), "Gen_Supply": bool(r[7])} for r in cur.fetchall()]


@app.get("/requisitions/{doc}/history")
def req_history(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Phase, Action, Action_Date, Action_By, Assigned_To, Comments "
                    "FROM REQUISITION.REQUISITION_HISTORY WHERE Document_Number = ? "
                    "ORDER BY History_ID ASC", (doc,))
        return [list(r) for r in cur.fetchall()]


_DEPT_SEND = {"kitchen": "Send_Kitchen", "household": "Send_Household",
              "it": "Send_IT", "maintenance": "Send_Maintenance"}
_DEPT_PROCESSED = {"kitchen": "Processed_Kitchen", "household": "Processed_Household",
                   "it": "Processed_IT", "maintenance": "Processed_Maintenance"}


@app.get("/requisitions/by-department/{dept}")
def list_by_department(dept: str, _: int = Depends(current_user_id)):
    send_col = _DEPT_SEND.get(dept.lower())
    proc_col = _DEPT_PROCESSED.get(dept.lower())
    if send_col is None:
        raise HTTPException(404, "Unknown department.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM REQUISITION.REQUISITION_TABLE "
            f"WHERE {send_col} = 1 AND Phase = 'Completed' AND {proc_col} = 0")
        return [list(r) for r in cur.fetchall()]
        
class ProcessReqIn(BaseModel):
    department: str
    doc_numbers: list[str] = []


@app.post("/requisitions/mark-processed")
def mark_processed(body: ProcessReqIn, _: int = Depends(current_user_id)):
    proc_col = _DEPT_PROCESSED.get(body.department.lower())
    if proc_col is None:
        raise HTTPException(404, "Unknown department.")
    if not body.doc_numbers:
        return {"updated": 0}
    with get_connection() as conn:
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in body.doc_numbers)
        cur.execute(
            f"UPDATE REQUISITION.REQUISITION_TABLE SET {proc_col} = 1 "
            f"WHERE Document_Number IN ({placeholders})",
            tuple(body.doc_numbers))
        conn.commit()
        return {"updated": cur.rowcount}

@app.put("/requisitions/{doc}")
def req_save(doc: str, body: SaveReqIn, caller: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, caller)
        cur.execute("SELECT Phase FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?", (doc,))
        prow = cur.fetchone()
        if prow is not None:
            cur.execute(f"UPDATE REQUISITION.REQUISITION_TABLE SET {_REQ_SET} "
                        "WHERE Document_Number=?", (*_req_params(body.fields), doc))
            phase, action = prow[0] or "Draft", "Updated"
        else:
            cur.execute(
                "INSERT INTO REQUISITION.REQUISITION_TABLE "
                "(Created_By, Document_Number, Site, Category, Maintenance, Department, "
                "Academic, Supplier, Purpose, Requesting, HOD_Comment, VP_Comment, "
                "Request_Type, Scope, Contractor, Material, VP_Approval, Principal_Comment, "
                "Maintenance_Unit, Trip_Date, Destination, Departure_Time, Cost, "
                "VP_Signature, Principal_Signature, Accounts_Acknowledged, "
                "Send_Kitchen, Send_Household, Send_IT, Send_Maintenance, Processed_Refs, Phase, "
                "Submit_Date, Assign_To) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (name, doc, *_req_params(body.fields), "Draft",
                 date.today().isoformat(), name))
            phase, action = "Draft", "Saved"
        _req_log_history(cur, doc, phase, action, name)
        _req_sync_items(cur, doc, body.items)
        conn.commit()
    return {"ok": True}


@app.post("/requisitions/{doc}/submit")
def req_submit(doc: str, body: SubmitReqIn, caller: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, caller)
        cur.execute("SELECT Phase, Assign_To, Category, Maintenance_Unit "
                    "FROM REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?", (doc,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Save the requisition before submitting.")
        current_phase, assign_to, category = row[0], row[1], row[2]
        maint = bool(body.fields.Maintenance_Unit)
        if (assign_to or "").strip() != (name or "").strip():
            raise HTTPException(403, "This requisition is not assigned to you.")
        if body.completed_phase != current_phase:
            raise HTTPException(409, "Phase changed - reload and try again.")
        phases = _form_phases(category, maint)
        idx = phases.index(current_phase) if current_phase in phases else 0
        if idx + 1 >= len(phases):
            raise HTTPException(409, "Already at the final phase.")
        natural_next = phases[idx + 1]
        allowed = [natural_next]
        if current_phase == "VP Review":
            allowed.append("Completed")
        requested = (body.next_phase or "").strip()
        next_phase = requested if requested in allowed else natural_next    
        
        
        approver_col = APPROVER_PHASE_COLUMN.get(current_phase)
        extra = f",{approver_col}=?" if approver_col else ""
        extra_params = (caller,) if approver_col else ()
        final_assignee = "" if next_phase == "Completed" else body.assignee
        cur.execute(
            f"UPDATE REQUISITION.REQUISITION_TABLE SET {_REQ_SET},"
            "Phase=?,Assign_To=?,Submit_Date=?,Complete_Date=?" + extra +
            " WHERE Document_Number=?",
            (*_req_params(body.fields), next_phase, final_assignee,
             date.today().isoformat(), date.today().isoformat(), *extra_params, doc))
        _req_log_history(cur, doc, current_phase, "Submitted", name,
                         final_assignee, body.comments)
        _req_sync_items(cur, doc, body.items)
        conn.commit()
    return {"next_phase": next_phase}


@app.get("/requisitions/{doc}/attachments")
def req_attachments(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Attachment_ID, File_Name, Uploaded_By, Upload_Date "
                    "FROM REQUISITION.REQUISITION_ATTACHMENTS WHERE Document_Number = ? "
                    "ORDER BY Upload_Date ASC", (doc,))
        return [list(r) for r in cur.fetchall()]


@app.post("/requisitions/{doc}/attachments")
def req_upload_attachment(doc: str, file: UploadFile = File(...),
                          caller: int = Depends(current_user_id)):
    key = f"{doc}/{uuid.uuid4().hex}_{file.filename}"
    dest = os.path.join(STORAGE_DIR, key)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        shutil.copyfileobj(file.file, fh)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO REQUISITION.REQUISITION_ATTACHMENTS "
                    "(Document_Number, File_Name, File_Path, Uploaded_By, Upload_Date) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (doc, file.filename, key, _caller_name(cur, caller),
                     date.today().isoformat()))
        conn.commit()
    return {"ok": True}


@app.get("/attachments/{att_id}/download")
def req_download_attachment(att_id: int, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT File_Name, File_Path FROM REQUISITION.REQUISITION_ATTACHMENTS "
                    "WHERE Attachment_ID = ?", (att_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "Attachment not found")
    path = os.path.join(STORAGE_DIR, row[1])
    if not os.path.exists(path):
        raise HTTPException(404, "File missing from storage")
    return FileResponse(path, filename=row[0])


@app.delete("/attachments/{att_id}")
def req_delete_attachment(att_id: int, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM REQUISITION.REQUISITION_ATTACHMENTS WHERE Attachment_ID = ?",
                    (att_id,))
        conn.commit()
    return {"ok": True}
    
import jwt
from datetime import datetime, timezone, timedelta

JWT_ALG = "HS256"
JWT_TTL_HOURS = 12
JWT_SECRET = os.environ.get("CTC_JWT_SECRET")
if not JWT_SECRET:
    if os.environ.get("CTC_DEV_AUTH") == "1":
        JWT_SECRET = "dev-only-insecure-secret"   # local convenience ONLY
    else:
        raise RuntimeError("CTC_JWT_SECRET must be set (no insecure default outside dev mode).")


def create_token(user_id, full_name=""):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "name": full_name or "",
         "iat": now, "exp": now + timedelta(hours=JWT_TTL_HOURS)},
        JWT_SECRET, algorithm=JWT_ALG)