"""Cross-platform file permission management."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def set_private_file(path: Path) -> None:
    """Set file permissions to owner-only read/write (0o600)."""
    if is_windows():
        _set_windows_private(path)
    else:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def set_private_dir(path: Path) -> None:
    """Set directory permissions to owner-only rwx (0o700)."""
    if is_windows():
        _set_windows_private_dir(path)
    else:
        path.chmod(stat.S_IRWXU)


def ensure_permissions(data_dir: Path, keys_dir: Path) -> list[str]:
    """Check and fix permissions for all sensitive files. Returns list of fixes applied."""
    fixes = []

    if is_windows():
        return fixes

    if not _check_dir_perm(keys_dir, stat.S_IRWXU):
        keys_dir.chmod(stat.S_IRWXU)
        fixes.append(f"Fixed directory permissions: {keys_dir}")

    for f in keys_dir.iterdir():
        if f.is_file() and not f.name.endswith(".pub"):
            if not _check_file_perm(f, stat.S_IRUSR | stat.S_IWUSR):
                f.chmod(stat.S_IRUSR | stat.S_IWUSR)
                fixes.append(f"Fixed private key permissions: {f.name}")

    return fixes


def _check_dir_perm(path: Path, expected: int) -> bool:
    try:
        return (path.stat().st_mode & 0o777) == expected
    except OSError:
        return False


def _check_file_perm(path: Path, expected: int) -> bool:
    try:
        return (path.stat().st_mode & 0o777) == expected
    except OSError:
        return False


def _set_windows_private(path: Path) -> None:
    """On Windows, remove inherited ACLs and grant only current user full control."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]

        # Get current user
        buf_size = ctypes.c_ulong(0)
        advapi32.GetUserNameW(None, ctypes.byref(buf_size))
        username = ctypes.create_unicode_buffer(buf_size.value)
        advapi32.GetUserNameW(username, ctypes.byref(buf_size))

        # Use icacls via subprocess as a reliable fallback
        import subprocess

        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username.value}:F"],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass  # Best effort on Windows


def _set_windows_private_dir(path: Path) -> None:
    _set_windows_private(path)
