"""Application configuration and data directory management."""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_NAME = "SSH Key Manager"
DATA_DIR_FILE = "data-dir.txt"
CONFIG_FILE = "config.json"
DB_FILE = "data.db"
KEYS_DIR = "keys"

VALID_DURATIONS = [1, 2, 4, 8, 24, 72]  # hours


def get_app_dir() -> Path:
    """Return the directory where the executable or script lives."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir_path(app_dir: Path) -> Path | None:
    """Read the data directory pointer file. Returns None if not set."""
    pointer = app_dir / DATA_DIR_FILE
    if pointer.exists():
        path_str = pointer.read_text(encoding="utf-8").strip()
        if path_str:
            p = Path(path_str)
            if p.is_absolute():
                return p
            return (app_dir / p).resolve()
    return None


def set_data_dir_path(app_dir: Path, data_dir: Path) -> None:
    """Write the data directory pointer file."""
    pointer = app_dir / DATA_DIR_FILE
    pointer.write_text(str(data_dir.resolve()), encoding="utf-8")


def init_data_dir(data_dir: Path) -> None:
    """Create data directory structure if it doesn't exist."""
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / KEYS_DIR).mkdir(exist_ok=True)


def load_config(data_dir: Path) -> dict:
    """Load application config from data directory."""
    cfg_path = data_dir / CONFIG_FILE
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_asset_path(filename: str) -> Path:
    """Resolve asset file path, works for both source and frozen builds."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / "assets" / filename


def save_config(data_dir: Path, config: dict) -> None:
    """Save application config to data directory."""
    cfg_path = data_dir / CONFIG_FILE
    cfg_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
