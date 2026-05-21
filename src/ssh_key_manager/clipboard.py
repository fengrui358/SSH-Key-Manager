"""Cross-platform clipboard operations."""

from __future__ import annotations

import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    try:
        if sys.platform == "darwin":
            proc = subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
            return proc.returncode == 0
        elif sys.platform == "win32":
            proc = subprocess.run(["clip"], input=text, text=True, timeout=5)
            return proc.returncode == 0
        else:
            # Linux: try xclip, then xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    proc = subprocess.run(cmd, input=text, text=True, timeout=5)
                    if proc.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except Exception:
        return False
