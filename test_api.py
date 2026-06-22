"""
test_api.py - boundary tests for the converted API.

These prove the permission decisions that moved from the desktop client to the
server actually hold: a non-admin can't manage users, a non-assignee can't
advance a requisition, a non-VP can't see everyone's requisitions, and a
request with no token is rejected before any database access.

Setup:
    pip install pytest httpx
    - Point DB_CONNECTION_STRING at a SEPARATE test database (NOT production)
      with the schema loaded.
    - Seed a few users + group memberships, then set the IDs/name below to match:
        ADMIN_ID      -> a member of the Administration group
        VP_ID         -> a member of the VP group (and not Administration)
        REQUESTER_ID  -> an ordinary user in neither
      REQUESTER_NAME must equal that user's "FirstName + ' ' + LastName".

Run:
    pytest test_api.py -v

How auth is faked: each test overrides current_user_id to return the id of the
user it wants to act as. require_admin and every query still run for real
against the test DB, so the authorization logic is genuinely exercised.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

import requisition_api as listapi
import requisition_form_api as formapi
import user_api as userapi

# Match these to your seeded test data.
ADMIN_ID       = 1
VP_ID          = 2
REQUESTER_ID   = 3
REQUESTER_NAME = "Test Requester"


def act_as(module, user_id):
    """Make subsequent requests to this app run as the given user."""
    module.app.dependency_overrides[module.current_user_id] = lambda: user_id


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    for m in (listapi, formapi, userapi):
        m.app.dependency_overrides.clear()


# ── User management is admin-only ──────────────────────────────────────────
def test_create_user_blocked_for_non_admin():
    act_as(userapi, REQUESTER_ID)
    client = TestClient(userapi.app)
    resp = client.post("/users", json={
        "first": "X", "last": "Y", "email": "x@y.z",
        "username": "xy", "password": "secret1"})
    assert resp.status_code == 403


def test_create_user_requires_password():
    act_as(userapi, ADMIN_ID)
    client = TestClient(userapi.app)
    resp = client.post("/users", json={
        "first": "X", "last": "Y", "email": "x@y.z", "username": "xy"})
    assert resp.status_code == 400


def test_missing_token_is_401():
    # No override, no Authorization header -> rejected before any DB access.
    client = TestClient(userapi.app)
    assert client.get("/users").status_code == 401


# ── Only the current assignee can advance a requisition ────────────────────
def _new_draft(doc):
    """Create a draft as the requester; the server makes them the assignee."""
    act_as(formapi, REQUESTER_ID)
    client = TestClient(formapi.app)
    body = {"fields": {"Category": "Household"}, "items": []}
    assert client.put(f"/requisitions/{doc}", json=body).status_code == 200
    return client


def test_submit_blocked_for_non_assignee():
    doc = f"TEST-{uuid.uuid4().hex[:8]}"
    _new_draft(doc)
    act_as(formapi, VP_ID)                       # not the assignee
    client = TestClient(formapi.app)
    resp = client.post(f"/requisitions/{doc}/submit", json={
        "fields": {"Category": "Household"}, "items": [],
        "assignee": "Someone Else", "completed_phase": "Draft"})
    assert resp.status_code == 403


def test_submit_advances_for_assignee():
    doc = f"TEST-{uuid.uuid4().hex[:8]}"
    client = _new_draft(doc)                     # still acting as the assignee
    resp = client.post(f"/requisitions/{doc}/submit", json={
        "fields": {"Category": "Household"}, "items": [],
        "assignee": REQUESTER_NAME, "completed_phase": "Draft"})
    assert resp.status_code == 200
    assert resp.json()["next_phase"] == "HOD Review"


def test_submit_rejects_stale_phase():
    doc = f"TEST-{uuid.uuid4().hex[:8]}"
    client = _new_draft(doc)
    resp = client.post(f"/requisitions/{doc}/submit", json={
        "fields": {"Category": "Household"}, "items": [],
        "assignee": REQUESTER_NAME, "completed_phase": "VP Review"})  # wrong phase
    assert resp.status_code == 409


# ── "View all" is enforced on the server, not the client ───────────────────
def test_view_all_downgraded_for_non_vp():
    act_as(listapi, REQUESTER_ID)
    client = TestClient(listapi.app)
    mine = client.get("/requisitions", params={"scope": "mine"}).json()
    asked_all = client.get("/requisitions", params={"scope": "all"}).json()
    # A non-VP asking for everything gets only their own rows.
    assert asked_all == mine
