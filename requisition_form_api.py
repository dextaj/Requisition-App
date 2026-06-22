"""
requisition_form_api.py - Application tier for the Requisition form.

Holds the queries RequisitionForm.pyw used to run. Highlights:

  * /requisitions/{doc}/submit is the approval action. The server reads the
    document's CURRENT phase and assignee, refuses unless the caller is that
    assignee, computes the next phase itself, and records the approver as the
    authenticated caller - not an id supplied by the client.
  * Attachments are stored centrally (local disk here; use Azure Blob Storage
    in production) and downloaded back through the API. The DB keeps only
    metadata + a storage key the client never sees.
  * On first save the server sets Created_By / Assign_To from the token, so the
    creator is the assignee of the new Draft and the submit check holds.

In production these endpoints plus auth_api / admin_api / requisition_api are
ONE FastAPI app (combine with APIRouter). Run:  uvicorn requisition_form_api:app
"""

import os
import re
import uuid
import shutil
import base64
from datetime import date

import pyodbc
from fastapi import (FastAPI, Depends, HTTPException, Query, Request,
                     UploadFile, File)
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

STORAGE_DIR = os.environ.get("CTC_ATTACH_DIR", "/home/site/attachments")

DOC_PREFIXES = {"Transport": "TRAN-", "Infrastructure": "INFR-",
                "Household": "HSLD-", "Kitchen": "KTCN-"}

PHASES_STANDARD    = ["Draft", "HOD Review", "VP Review",
                      "Principal Approval", "Procurement", "Accounts"]
PHASES_MAINTENANCE = ["Draft", "HOD Review", "VP Review", "Maintenance Unit",
                      "VP Approval", "Principal Approval", "Procurement", "Accounts"]
PHASES_TRANSPORT   = ["Draft", "HOD Review", "VP Approval", "Accounts"]

APPROVER_PHASE_COLUMN = {
    "HOD Review":         "HOD_Approver_ID",
    "VP Review":          "VP_Approver_ID",
    "VP Approval":        "VP_Approver_ID",
    "Principal Approval": "Principal_Approver_ID",
}


def get_phases(category, via_maintenance=False):
    if category == "Transport":
        return PHASES_TRANSPORT
    if via_maintenance:
        return PHASES_MAINTENANCE
    return PHASES_STANDARD


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


def _caller_name(cur, user_id):
    cur.execute("SELECT FirstName + ' ' + LastName "
                "FROM Administration.Users WHERE UserID = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None


# ── Payload shapes ─────────────────────────────────────────────────────────
class ReqFields(BaseModel):
    Site: str = "";            Category: str = "";       Maintenance: str = ""
    Department: str = "";      Academic: str = "";       Supplier: str = ""
    Purpose: str = "";         Requesting: str = "";     HOD_Comment: str = ""
    VP_Comment: str = "";      Request_Type: str = "";   Scope: str = ""
    Contractor: str = "";      Material: str = "";       VP_Approval: str = ""
    Principal_Comment: str = ""; Maintenance_Unit: int = 0
    Trip_Date: str = "";       Destination: str = "";    Departure_Time: str = ""
    Cost: str = "";            VP_Signature: str = "";   Principal_Signature: str = ""
    Accounts_Acknowledged: int = 0


class Item(BaseModel):
    Item_Name: str = "";  Amt_In_Stock: str = "";  Quantity_Requested: str = ""
    Comments: str = "";   Broiler: int = 0;  Layer: int = 0
    Pigs: int = 0;        Gen_Supply: int = 0


class SaveIn(BaseModel):
    fields: ReqFields
    items: list[Item] = []


class SubmitIn(BaseModel):
    fields: ReqFields
    items: list[Item] = []
    assignee: str
    completed_phase: str
    comments: str = ""


_SET = ("Site=?,Category=?,Maintenance=?,Department=?,Academic=?,Supplier=?,"
        "Purpose=?,Requesting=?,HOD_Comment=?,VP_Comment=?,Request_Type=?,Scope=?,"
        "Contractor=?,Material=?,VP_Approval=?,Principal_Comment=?,Maintenance_Unit=?,"
        "Trip_Date=?,Destination=?,Departure_Time=?,Cost=?,VP_Signature=?,"
        "Principal_Signature=?,Accounts_Acknowledged=?")


def _field_params(f: ReqFields):
    return (f.Site, f.Category, f.Maintenance, f.Department, f.Academic,
            f.Supplier, f.Purpose, f.Requesting, f.HOD_Comment, f.VP_Comment,
            f.Request_Type, f.Scope, f.Contractor, f.Material, f.VP_Approval,
            f.Principal_Comment, f.Maintenance_Unit, f.Trip_Date, f.Destination,
            f.Departure_Time, f.Cost, f.VP_Signature, f.Principal_Signature,
            f.Accounts_Acknowledged)


def _log_history(cur, doc, phase, action, action_by, assigned_to="", comments=""):
    cur.execute(
        "INSERT INTO REQUISITION.REQUISITION_HISTORY "
        "(Document_Number, Phase, Action, Action_Date, Action_By, "
        "Assigned_To, Comments) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc, phase, action, date.today().isoformat(),
         action_by, assigned_to, comments))


def _sync_items(cur, doc, items):
    cur.execute("DELETE FROM REQUISITION.REQUISITION_ITEMS "
                "WHERE Document_Number = ?", (doc,))
    for d in items:
        cur.execute(
            "INSERT INTO REQUISITION.REQUISITION_ITEMS "
            "(Document_Number, Item_Name, Amt_In_Stock, Quantity_Requested, "
            "Comments, Broiler, Layer, Pigs, Gen_Supply) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (doc, d.Item_Name, d.Amt_In_Stock, d.Quantity_Requested, d.Comments,
             d.Broiler, d.Layer, d.Pigs, d.Gen_Supply))


# ── Lookups ────────────────────────────────────────────────────────────────
@app.get("/lists")
def lists(_: int = Depends(current_user_id)):
    out = {}
    with get_connection() as conn:
        cur = conn.cursor()
        for key, table in (("site", "Site"), ("category", "Category"),
                           ("maintenance", "Maintenance"),
                           ("department", "Department"), ("academic", "Academic")):
            # isActive filter mirrors the original query exactly.
            cur.execute(f"SELECT KeywordName FROM Keywords.{table} "
                        f"WHERE isActive = 0 ORDER BY KeywordName")
            out[key] = [r[0] for r in cur.fetchall()]
    return out


@app.get("/users")
def users(_: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT FirstName, LastName FROM Administration.Users")
        return [f"{r[0]} {r[1]}" for r in cur.fetchall()]


@app.get("/doc-number")
def doc_number(category: str = "", _: int = Depends(current_user_id)):
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
            nums = re.findall(r"\d+", row[0])
            counter = int(nums[-1]) if nums else 0
    return {"doc_number": f"{prefix}{counter + 1:05d}"}


# ── Requisition reads ──────────────────────────────────────────────────────
@app.get("/requisitions/{doc}")
def get_requisition(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?", (doc,))
        row = cur.fetchone()
        if row is None:
            return None
        # Keyed by column name so the form's row.get("Created_By") still works.
        return {d[0]: v for d, v in zip(cur.description, row)}


@app.get("/requisitions/{doc}/items")
def items(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT Item_Name, Amt_In_Stock, Quantity_Requested, Comments, "
            "Broiler, Layer, Pigs, Gen_Supply FROM REQUISITION.REQUISITION_ITEMS "
            "WHERE Document_Number = ? ORDER BY Item_ID ASC", (doc,))
        return [{"Item_Name": r[0] or "", "Amt_In_Stock": r[1] or "",
                 "Quantity_Requested": r[2] or "", "Comments": r[3] or "",
                 "Broiler": bool(r[4]), "Layer": bool(r[5]),
                 "Pigs": bool(r[6]), "Gen_Supply": bool(r[7])}
                for r in cur.fetchall()]


@app.get("/requisitions/{doc}/history")
def history(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT Phase, Action, Action_Date, Action_By, Assigned_To, Comments "
            "FROM REQUISITION.REQUISITION_HISTORY WHERE Document_Number = ? "
            "ORDER BY History_ID ASC", (doc,))
        return [list(r) for r in cur.fetchall()]


@app.get("/requisitions/{doc}/approvers")
def approvers(doc: str, _: int = Depends(current_user_id)):
    result = {"hod": None, "vp": None, "principal": None}
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT HOD_Approver_ID, VP_Approver_ID, Principal_Approver_ID "
                    "FROM REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?", (doc,))
        row = cur.fetchone()
        if not row:
            return result
        for key, uid in zip(("hod", "vp", "principal"), (row[0], row[1], row[2])):
            if not uid:
                continue
            cur.execute("SELECT FirstName + ' ' + LastName "
                        "FROM Administration.Users WHERE UserID = ?", (uid,))
            nrow = cur.fetchone()
            cur.execute("SELECT SignatureData FROM Administration.UserSignatures "
                        "WHERE UserID = ?", (uid,))
            srow = cur.fetchone()
            img = (base64.b64encode(bytes(srow[0])).decode("ascii")
                   if srow and srow[0] is not None else None)
            result[key] = {"name": nrow[0] if nrow else "", "image": img}
    return result


# ── Save (draft) ───────────────────────────────────────────────────────────
@app.put("/requisitions/{doc}")
def save_requisition(doc: str, body: SaveIn, caller: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, caller)
        cur.execute("SELECT Phase FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?", (doc,))
        prow = cur.fetchone()
        exists = prow is not None

        if exists:
            cur.execute(f"UPDATE REQUISITION.REQUISITION_TABLE SET {_SET} "
                        "WHERE Document_Number=?",
                        (*_field_params(body.fields), doc))
            phase, action = prow[0] or "Draft", "Updated"
        else:
            # Created_By and Assign_To come from the token, not the client.
            cur.execute(
                "INSERT INTO REQUISITION.REQUISITION_TABLE "
                "(Created_By, Document_Number, Site, Category, Maintenance, "
                "Department, Academic, Supplier, Purpose, Requesting, HOD_Comment, "
                "VP_Comment, Request_Type, Scope, Contractor, Material, VP_Approval, "
                "Principal_Comment, Maintenance_Unit, Trip_Date, Destination, "
                "Departure_Time, Cost, VP_Signature, Principal_Signature, "
                "Accounts_Acknowledged, Phase, Submit_Date, Assign_To) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (name, doc, *_field_params(body.fields),
                 "Draft", date.today().isoformat(), name))
            phase, action = "Draft", "Saved"

        _log_history(cur, doc, phase, action, name)
        _sync_items(cur, doc, body.items)
        conn.commit()
    return {"ok": True}


# ── Submit (advance phase) - the authorization-critical action ─────────────
@app.post("/requisitions/{doc}/submit")
def submit_requisition(doc: str, body: SubmitIn, caller: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        name = _caller_name(cur, caller)
        cur.execute("SELECT Phase, Assign_To, Category, Maintenance_Unit "
                    "FROM REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?", (doc,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Save the requisition before submitting.")
        current_phase, assign_to, category, maint = row[0], row[1], row[2], bool(row[3])

        # Only the person the document is currently assigned to may advance it.
        if (assign_to or "").strip() != (name or "").strip():
            raise HTTPException(403, "This requisition is not assigned to you.")
        # The client must be completing the phase the document is actually in.
        if body.completed_phase != current_phase:
            raise HTTPException(409, "Phase changed - reload and try again.")

        phases = get_phases(category, maint)
        idx = phases.index(current_phase) if current_phase in phases else 0
        if idx + 1 >= len(phases):
            raise HTTPException(409, "Already at the final phase.")
        next_phase = phases[idx + 1]

        # Record the submitting user as the approver for the completed phase.
        approver_col = APPROVER_PHASE_COLUMN.get(current_phase)
        extra = f",{approver_col}=?" if approver_col else ""
        extra_params = (caller,) if approver_col else ()

        cur.execute(
            f"UPDATE REQUISITION.REQUISITION_TABLE SET {_SET},"
            "Phase=?,Assign_To=?,Submit_Date=?,Complete_Date=?" + extra +
            " WHERE Document_Number=?",
            (*_field_params(body.fields), next_phase, body.assignee,
             date.today().isoformat(), date.today().isoformat(),
             *extra_params, doc))
        _log_history(cur, doc, current_phase, "Submitted", name,
                     body.assignee, body.comments)
        _sync_items(cur, doc, body.items)
        conn.commit()
    return {"next_phase": next_phase}


# ── Attachments (stored centrally; metadata + storage key in the DB) ───────
@app.get("/requisitions/{doc}/attachments")
def list_attachments(doc: str, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT Attachment_ID, File_Name, Uploaded_By, Upload_Date "
            "FROM REQUISITION.REQUISITION_ATTACHMENTS WHERE Document_Number = ? "
            "ORDER BY Upload_Date ASC", (doc,))
        return [list(r) for r in cur.fetchall()]


@app.post("/requisitions/{doc}/attachments")
def upload_attachment(doc: str, file: UploadFile = File(...),
                      caller: int = Depends(current_user_id)):
    # Local disk here; in production write to Azure Blob Storage and store the
    # blob name as the key. The client never sees this path.
    key = f"{doc}/{uuid.uuid4().hex}_{file.filename}"
    dest = os.path.join(STORAGE_DIR, key)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        shutil.copyfileobj(file.file, fh)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO REQUISITION.REQUISITION_ATTACHMENTS "
            "(Document_Number, File_Name, File_Path, Uploaded_By, Upload_Date) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc, file.filename, key, _caller_name(cur, caller),
             date.today().isoformat()))
        conn.commit()
    return {"ok": True}


@app.get("/attachments/{att_id}/download")
def download_attachment(att_id: int, _: int = Depends(current_user_id)):
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
def remove_attachment(att_id: int, _: int = Depends(current_user_id)):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM REQUISITION.REQUISITION_ATTACHMENTS "
                    "WHERE Attachment_ID = ?", (att_id,))
        conn.commit()
    return {"ok": True}
