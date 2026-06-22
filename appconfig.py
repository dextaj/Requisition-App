"""Per-customer configuration for the Church Teachers College app suite.

One codebase serves several customers, each with its own database. The active
customer is chosen, in priority order, by:

  1. a `--customer KEY` command-line argument — put this on the published
     RemoteApp shortcut, one per customer; then
  2. the CTC_CUSTOMER environment variable — inherited by the screens that the
     login launches, so a whole session stays on one customer; then
  3. the key "default".

Connection details live in customers.json (next to this file, or wherever
CTC_CONFIG_FILE points), so adding a customer needs no code change. If no
registry file exists and the key is "default", a built-in fallback pointing at
the original Chris / ChurchTeachersCollegeDB database is used, so the suite
still runs as before during single-customer development.

SECURITY NOTE: with Windows (Trusted) auth the registry holds only server and
database names — not secrets. If you switch a customer to SQL auth by adding
"username"/"password" entries, that file then contains credentials and must NOT
be world-readable on a shared host. Prefer restrictive per-file permissions, an
encrypted store, or fetching credentials from a service at startup.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

_CONFIG_FILE_ENV = "CTC_CONFIG_FILE"
_CUSTOMER_ENV    = "CTC_CUSTOMER"
_DEFAULT_FILE    = "customers.json"
_DEFAULT_KEY     = "default"


class ConfigError(Exception):
    """Raised when the active customer cannot be determined or loaded."""


@dataclass(frozen=True)
class CustomerConfig:
    key: str
    display_name: str
    server: str
    database: str
    driver: str = "ODBC Driver 18 for SQL Server"
    encrypt: str = "Optional"          # use "Mandatory" once traffic leaves the LAN
    username: str | None = None        # set => SQL auth; None => Windows auth
    password: str | None = None

    def connection_string(self) -> str:
        parts = [
            f"Driver={self.driver};",
            f"Server={self.server};",
            f"Database={self.database};",
            f"encrypt={self.encrypt};",
        ]
        if self.username:
            parts.append(f"UID={self.username};")
            parts.append(f"PWD={self.password or ''};")
        else:
            parts.append("Trusted_Connection=yes;")
        return "".join(parts)


# Used only when no customers.json exists and the key is "default", so the
# suite keeps working out of the box. Honors the older CTC_DB_* overrides.
_BUILTIN_DEFAULT = CustomerConfig(
    key=_DEFAULT_KEY,
    display_name="Church Teachers College",
    server=os.environ.get("CTC_DB_SERVER", "Chris"),
    database=os.environ.get("CTC_DB_NAME", "ChurchTeachersCollegeDB"),
)

_cache: CustomerConfig | None = None


def _registry_path() -> Path:
    override = os.environ.get(_CONFIG_FILE_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / _DEFAULT_FILE


def _customer_key(argv) -> str:
    args = argv[1:]
    for i, tok in enumerate(args):
        if tok == "--customer" and i + 1 < len(args):
            return args[i + 1]
        if tok.startswith("--customer="):
            return tok.split("=", 1)[1]
    return os.environ.get(_CUSTOMER_ENV) or _DEFAULT_KEY


def _build(key: str, entry: dict) -> CustomerConfig:
    try:
        return CustomerConfig(
            key=key,
            display_name=entry.get("display_name", key),
            server=entry["server"],
            database=entry["database"],
            driver=entry.get("driver", "ODBC Driver 18 for SQL Server"),
            encrypt=entry.get("encrypt", "Optional"),
            username=entry.get("username"),
            password=entry.get("password"),
        )
    except KeyError as exc:
        raise ConfigError(
            f"Customer '{key}' is missing required field {exc} in the registry")


def active_config(argv=None, *, reload=False) -> CustomerConfig:
    """Resolve (and cache) the active customer's configuration."""
    global _cache
    if _cache is not None and not reload:
        return _cache

    key = _customer_key(sys.argv if argv is None else argv)
    path = _registry_path()

    if not path.exists():
        if key == _DEFAULT_KEY:
            _cache = _BUILTIN_DEFAULT
            _export(_cache.key)
            return _cache
        raise ConfigError(
            f"Customer '{key}' requested but no registry file at {path}.")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            registry = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Could not read customer registry {path}: {exc}")

    customers = registry.get("customers", {})
    entry = customers.get(key)
    if entry is None:
        known = ", ".join(sorted(customers)) or "(none)"
        raise ConfigError(f"Unknown customer '{key}'. Known customers: {known}")

    _cache = _build(key, entry)
    _export(_cache.key)
    return _cache


def _export(key: str) -> None:
    """Record the active customer in this process's environment so that child
    screens launched with a normal (inherited) environment pick it up — no need
    to pass --customer or replace the child's environment."""
    os.environ[_CUSTOMER_ENV] = key


def child_env() -> dict:
    """Deprecated: customer propagation now happens via the inherited
    environment (see _export). Kept only so any external caller still works;
    returns a full copy of the current environment with the customer set."""
    active_config()
    return dict(os.environ)
