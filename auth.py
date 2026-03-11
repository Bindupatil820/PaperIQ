import hashlib
import json
import secrets
from pathlib import Path
from datetime import datetime

USERS_FILE = Path(__file__).resolve().parent / "users.json"
LOGIN_HISTORY_FILE = Path(__file__).resolve().parent / "login_history.json"

# Default seeded users (passwords are only used on first initialization).
DEFAULT_USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "researcher": {"password": "research123", "role": "Researcher"},
    "user": {"password": "user123", "role": "User"},
}


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def _encode_user(password: str, role: str) -> dict:
    salt = secrets.token_hex(16)
    return {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "role": role,
    }


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if isinstance(users, dict):
                changed = False
                # Backward-compat: migrate plain passwords if present.
                for uname, record in list(users.items()):
                    if not isinstance(record, dict):
                        users.pop(uname, None)
                        changed = True
                        continue
                    if "password" in record and "password_hash" not in record:
                        users[uname] = _encode_user(record.get("password", ""), record.get("role", "User"))
                        changed = True
                if changed:
                    _save_users(users)
                return users
        except Exception:
            pass

    users = {
        username: _encode_user(data["password"], data["role"])
        for username, data in DEFAULT_USERS.items()
    }
    _save_users(users)
    return users


def authenticate(username: str, password: str) -> tuple[bool, str]:
    users = _load_users()
    uname = _normalize_username(username)
    user = users.get(uname)
    if not user:
        return False, "User"
    salt = user.get("salt", "")
    expected = user.get("password_hash", "")
    actual = _hash_password(password or "", salt)
    if actual != expected:
        return False, user.get("role", "User")
    return True, user.get("role", "User")


def register_user(username: str, password: str, role: str) -> tuple[bool, str]:
    uname = _normalize_username(username)
    if len(uname) < 3:
        return False, "Username must be at least 3 characters."
    if not uname.replace("_", "").replace("-", "").isalnum():
        return False, "Username can only contain letters, numbers, '-' and '_'."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."
    if role not in {"User", "Researcher"}:
        return False, "Only User and Researcher accounts can be self-created."

    users = _load_users()
    if uname in users:
        return False, "Username already exists. Choose a different username."

    users[uname] = _encode_user(password, role)
    _save_users(users)
    return True, "Account created successfully. You can sign in now."


def _load_login_history() -> dict:
    """Load login history from JSON file."""
    if LOGIN_HISTORY_FILE.exists():
        try:
            return json.loads(LOGIN_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"logins": [], "sessions": []}


def _save_login_history(history: dict) -> None:
    """Save login history to JSON file."""
    LOGIN_HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def log_login(username: str, role: str) -> None:
    """Log a successful login attempt."""
    history = _load_login_history()
    login_entry = {
        "username": username,
        "role": role,
        "timestamp": datetime.now().isoformat(),
        "action": "login"
    }
    history["logins"].insert(0, login_entry)
    # Keep only last 100 login records
    history["logins"] = history["logins"][:100]
    _save_login_history(history)


def log_logout(username: str) -> None:
    """Log a logout attempt."""
    history = _load_login_history()
    logout_entry = {
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "action": "logout"
    }
    history["logins"].insert(0, logout_entry)
    # Keep only last 100 records
    history["logins"] = history["logins"][:100]
    _save_login_history(history)


def get_login_history(limit: int = 50) -> list:
    """Get recent login history."""
    history = _load_login_history()
    return history.get("logins", [])[:limit]


def get_registered_users() -> dict:
    """Get all registered users (without passwords)."""
    users = _load_users()
    result = {}
    for username, data in users.items():
        result[username] = {
            "role": data.get("role", "User"),
            "created": "N/A"  # We don't track creation date currently
        }
    return result

