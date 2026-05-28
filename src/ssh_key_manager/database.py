"""SQLite database operations for SSH keys and servers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def get_db_path(data_dir: Path) -> Path:
    return data_dir / "data.db"


def connect(data_dir: Path) -> sqlite3.Connection:
    db_path = get_db_path(data_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 22,
            username TEXT NOT NULL,
            auth_type TEXT NOT NULL DEFAULT 'password',
            stored_key_path TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ssh_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            public_key_path TEXT NOT NULL,
            private_key_path TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
        );
    """)
    _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Add missing columns to tables created with older schema versions."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(servers)").fetchall()}
    if "auth_type" not in cols:
        conn.execute("ALTER TABLE servers ADD COLUMN auth_type TEXT NOT NULL DEFAULT 'password'")
    if "stored_key_path" not in cols:
        conn.execute("ALTER TABLE servers ADD COLUMN stored_key_path TEXT")


# --- Server operations ---


def add_server(
    conn: sqlite3.Connection,
    name: str,
    host: str,
    port: int,
    username: str,
    auth_type: str = "password",
    stored_key_path: str | None = None,
) -> int:
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO servers (name, host, port, username, auth_type, stored_key_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, host, port, username, auth_type, stored_key_path, now),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def list_servers(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM servers ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_server(conn: sqlite3.Connection, server_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
    return dict(row) if row else None


def delete_server(conn: sqlite3.Connection, server_id: int) -> bool:
    cur = conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    return cur.rowcount > 0


def update_server(
    conn: sqlite3.Connection,
    server_id: int,
    name: str,
    host: str,
    port: int,
    username: str,
    auth_type: str = "password",
    stored_key_path: str | None = None,
) -> bool:
    cur = conn.execute(
        """UPDATE servers SET name=?, host=?, port=?, username=?, auth_type=?, stored_key_path=?
           WHERE id=?""",
        (name, host, port, username, auth_type, stored_key_path, server_id),
    )
    conn.commit()
    return cur.rowcount > 0


# --- Key operations ---


def add_key(
    conn: sqlite3.Connection,
    server_id: int,
    key_name: str,
    public_key_path: str,
    private_key_path: str,
    duration_hours: int,
) -> int:
    now = _now_iso()
    from datetime import timedelta

    if duration_hours == 0:
        expires = "9999-12-31T23:59:59+00:00"
    else:
        expires = (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).isoformat()
    cur = conn.execute(
        """INSERT INTO ssh_keys
           (server_id, key_name, public_key_path, private_key_path, duration_hours, created_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (server_id, key_name, public_key_path, private_key_path, duration_hours, now, expires),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def list_keys(conn: sqlite3.Connection, include_revoked: bool = False) -> list[dict]:
    sql = """
        SELECT k.*, s.name as server_name, s.host as server_host, s.username as server_username, s.port as server_port
        FROM ssh_keys k
        JOIN servers s ON k.server_id = s.id
    """
    if not include_revoked:
        sql += " WHERE k.revoked_at IS NULL"
    sql += " ORDER BY k.created_at DESC"
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def get_key(conn: sqlite3.Connection, key_id: int) -> dict | None:
    row = conn.execute(
        """SELECT k.*, s.name as server_name, s.host as server_host, s.username as server_username, s.port as server_port
           FROM ssh_keys k
           JOIN servers s ON k.server_id = s.id
           WHERE k.id = ?""",
        (key_id,),
    ).fetchone()
    return dict(row) if row else None


def revoke_key(conn: sqlite3.Connection, key_id: int) -> bool:
    cur = conn.execute(
        "UPDATE ssh_keys SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
        (_now_iso(), key_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_key(conn: sqlite3.Connection, key_id: int) -> bool:
    cur = conn.execute("DELETE FROM ssh_keys WHERE id = ?", (key_id,))
    conn.commit()
    return cur.rowcount > 0


def list_keys_by_server(conn: sqlite3.Connection, server_id: int) -> list[dict]:
    """List all non-revoked keys for a specific server."""
    rows = conn.execute(
        """SELECT k.*, s.name as server_name, s.host as server_host, s.username as server_username, s.port as server_port
           FROM ssh_keys k
           JOIN servers s ON k.server_id = s.id
           WHERE k.server_id = ? AND k.revoked_at IS NULL
           ORDER BY k.created_at DESC""",
        (server_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_expired_keys(conn: sqlite3.Connection) -> list[dict]:
    now = _now_iso()
    rows = conn.execute(
        """SELECT k.*, s.name as server_name, s.host as server_host, s.username as server_username, s.port as server_port
           FROM ssh_keys k
           JOIN servers s ON k.server_id = s.id
           WHERE k.expires_at <= ? AND k.revoked_at IS NULL""",
        (now,),
    ).fetchall()
    return [dict(r) for r in rows]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def store_key_path(data_dir: Path, absolute_path: Path) -> str:
    """Convert an absolute key file path to a data-dir-relative path for DB storage.

    This makes key paths portable when the data directory is synced across
    machines with different absolute paths.
    """
    return str(absolute_path.resolve().relative_to(data_dir.resolve()))


def resolve_key_path(data_dir: Path, stored_path: str | None) -> Path | None:
    """Resolve a stored key path to an absolute path.

    Handles both relative paths (current format) and absolute paths
    (legacy format from older versions or synced databases). If an
    absolute path doesn't exist, falls back to looking in the data
    directory's keys/servers folder.
    """
    if not stored_path:
        return None
    p = Path(stored_path)
    if p.is_absolute():
        if p.exists():
            return p
        # Legacy absolute path from a different machine — try to find
        # the file by its name in the data directory
        fallback = data_dir / "keys" / "servers" / p.name
        if fallback.exists():
            return fallback
        # Return the path as-is; caller should handle missing files
        return p
    return (data_dir / p).resolve()
