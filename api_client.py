"""
api_client.py - the only client-side module that knows the API exists.

The login window imports this instead of pyodbc. No database driver, no
connection string, and no password hashes ever live on the user's PC.

Defaults to your local API (http://localhost:8000). Later, point it at Azure
by setting CTC_API_BASE - no code change needed.
"""

import os

import requests

API_BASE = os.environ.get("CTC_API_BASE", "http://localhost:8000").rstrip("/")

_session = requests.Session()
_token = None


def login(username, password, os_user=None):
    """Return the user dict on success, or None on bad credentials.

    Raises on connection/server errors so the UI can show a clear message.
    """
    global _token
    resp = _session.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password, "os_user": os_user},
        timeout=30,
    )
    if resp.status_code == 401:
        return None
    resp.raise_for_status()
    data = resp.json()
    _token = data["token"]
    # Every later call automatically carries the token.
    _session.headers["Authorization"] = f"Bearer {_token}"
    return data


def set_token(token):
    global _token
    _token = token
    _session.headers["Authorization"] = f"Bearer {token}"


def token():
    return _token
