"""
Secure password storage via keyring (Windows Credential Manager on Windows).

Simple API:
- set_password(username: str, password: str) -> None
- get_password(username: str) -> str | None
- delete_password(username: str) -> None

Notes for PyInstaller packaging (no code changes required):
- PyInstaller usually detects keyring backends, but if you see runtime backend import errors,
  add a hidden import for Windows backend in your spec or command:
  hiddenimports=["keyring.backends.Windows"]
- Scheduled task should run under the same user context to access the stored credential.
"""
from __future__ import annotations

from typing import Optional
import keyring  # type: ignore
from keyring.errors import PasswordDeleteError

SERVICE_NAME = "CSU_WIFI_AutoLogin"


def set_password(username: str, password: str) -> None:
    """Store password for the given username in the system credential store."""
    if not username:
        raise ValueError("username must not be empty")
    keyring.set_password(SERVICE_NAME, username, password)


def get_password(username: str) -> Optional[str]:
    """Retrieve stored password for username, or None if not found."""
    if not username:
        return None
    try:
        return keyring.get_password(SERVICE_NAME, username)
    except Exception:
        return None


def delete_password(username: str) -> None:
    """Delete stored password for username. No-op if not found."""
    if not username:
        return
    try:
        keyring.delete_password(SERVICE_NAME, username)
    except PasswordDeleteError:
        # Not found; safely ignore
        return
    except Exception:
        # Ignore other backend-specific issues silently
        return

