# security_core.py
import os
import json
import getpass
import threading
from datetime import datetime
from typing import Optional

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
AUDIT_LOG = os.path.join(BASE_DIR, "security_audit.log")

_SESSION = {"user": None, "started_at": None, "session_id": None}

def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def _now_iso():
    return datetime.now().isoformat(sep=" ", timespec="seconds")

def audit(event: str, details: str = ""):
    """
    Write a structured audit line:
      timestamp | event | user | details
    details is a free text (prefer JSON for structured data).
    """
    ensure_base_dir()
    user = get_current_user()
    ts = _now_iso()
    line = f"{ts} | {event} | {user} | {details}\n"
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Do not crash the app for logging failures
        pass

def get_current_user():
    # Prefer session user if set, otherwise OS user
    sess_user = _SESSION.get("user")
    if sess_user:
        return sess_user
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"

# ---- Session helpers ----
def start_user_session(user: Optional[str] = None):
    """
    Register a session start for the operator.
    """
    ensure_base_dir()
    if user:
        _SESSION["user"] = user
    else:
        try:
            _SESSION["user"] = getpass.getuser()
        except Exception:
            _SESSION["user"] = "unknown"
    _SESSION["started_at"] = _now_iso()
    _SESSION["session_id"] = f"{_SESSION['user']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    audit("session_started", json.dumps({"session_id": _SESSION["session_id"], "user": _SESSION["user"], "started_at": _SESSION["started_at"]}))

def end_user_session():
    sid = _SESSION.get("session_id")
    audit("session_ended", json.dumps({"session_id": sid}))
    _SESSION["user"] = None
    _SESSION["started_at"] = None
    _SESSION["session_id"] = None

# ---- Module / navigation helpers ----
def module_opened(module_name: str, details: str = ""):
    audit("module_opened", json.dumps({"module": module_name, "details": details}))

def module_closed(module_name: str, details: str = ""):
    audit("module_closed", json.dumps({"module": module_name, "details": details}))

def button_clicked(module_name: str, button_name: str, details: str = ""):
    audit("button_clicked", json.dumps({"module": module_name, "button": button_name, "details": details}))

def view_attempt(module_name: str, item: str, success: bool, reason: str = ""):
    audit("view_attempt", json.dumps({"module": module_name, "item": item, "success": success, "reason": reason}))

# ---- Clipboard helper with auto-clear ----
def copy_to_clipboard_then_clear(root, text: str, seconds: int = 15):
    """
    Copy text to clipboard and clear it after `seconds`. Audit both actions.
    """
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        audit("copy_to_clipboard", f"len={len(text)}")
    except Exception:
        pass

    def clear():
        try:
            root.clipboard_clear()
            audit("clipboard_cleared", "")
        except Exception:
            pass
    t = threading.Timer(seconds, clear)
    t.daemon = True
    t.start()