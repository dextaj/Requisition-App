"""Shared logging for the Church Teachers College app suite.

Writes to a rotating log file so problems on the hosted server leave a record,
and also echoes to the console *when one is attached* (i.e. when started with
`python ...`, not `pythonw`/RemoteApp). Use:

    import applog
    log = applog.get_logger("login")
    log.info("signed in")
    log.exception("query failed")   # inside an except: includes the traceback

Log file location (first that works):
    %LOCALAPPDATA%\\ChurchTeachersCollege\\logs\\app.log   (per Windows user)
    else a 'logs' folder next to this module.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_configured = False


def _log_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    candidate = (Path(base) / "ChurchTeachersCollege" / "logs"
                 if base else Path(__file__).resolve().parent / "logs")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except OSError:
        return Path(__file__).resolve().parent


def _configure() -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger("ctc")
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(name)s  %(message)s")

    try:
        fh = RotatingFileHandler(
            _log_dir() / "app.log",
            maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass  # if the file can't be opened, carry on with console only

    # Console handler only when stderr exists (absent under pythonw/RemoteApp).
    if sys.stderr is not None:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

    if not root.handlers:           # never leave a logger with no handler
        root.addHandler(logging.NullHandler())

    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"ctc.{name}")
