"""SSH key generation and lifecycle management."""

from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import nacl.signing

from . import database
from .permissions import set_private_dir, set_private_file


def generate_key(data_dir: Path, conn, server_id: int, duration_hours: int, label: str = "") -> dict:
    """Generate an ed25519 key pair, save to data_dir/keys/, and register in DB."""
    from datetime import timedelta

    keys_dir = data_dir / "keys"
    keys_dir.mkdir(exist_ok=True)
    set_private_dir(keys_dir)

    key_id_str = uuid.uuid4().hex[:12]
    key_name = label or f"key_{key_id_str}"
    priv_path = keys_dir / f"id_ed25519_{key_id_str}"
    pub_path = keys_dir / f"id_ed25519_{key_id_str}.pub"

    expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

    # Generate ed25519 key using cryptography library
    private_key = Ed25519PrivateKey.generate()

    # Write private key in OpenSSH format
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    priv_path.write_bytes(priv_pem)
    set_private_file(priv_path)

    # Build and write public key in OpenSSH format
    raw_private = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    signing_key = nacl.signing.SigningKey(raw_private)
    verify_key = signing_key.verify_key

    # SSH wire format: string "ssh-ed25519" + string(32-byte pubkey)
    key_type = b"ssh-ed25519"
    pub_blob = (
        len(key_type).to_bytes(4, "big") + key_type +
        len(bytes(verify_key)).to_bytes(4, "big") + bytes(verify_key)
    )
    pub_b64 = base64.b64encode(pub_blob).decode()

    # Comment with metadata: label, tool, expiry time
    expires_str = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    comment = f"{key_name}_ssh-key-manager_expires={expires_str}"
    pub_path.write_text(f"ssh-ed25519 {pub_b64} {comment}\n", encoding="utf-8")

    # Register in database
    db_id = database.add_key(
        conn,
        server_id=server_id,
        key_name=key_name,
        public_key_path=str(pub_path),
        private_key_path=str(priv_path),
        duration_hours=duration_hours,
    )

    return database.get_key(conn, db_id)  # type: ignore[return-value]


def revoke_key(data_dir: Path, conn, key_id: int, ssh_deploy_func=None) -> tuple[bool, str]:
    """Revoke a key: remove from server and delete local files."""
    key = database.get_key(conn, key_id)
    if not key:
        return False, "Key not found"

    if key.get("revoked_at"):
        return False, "Key already revoked"

    messages = []

    # Try to remove from server
    if ssh_deploy_func:
        try:
            ssh_deploy_func(
                host=key["server_host"],
                username=key["server_username"],
                port=22,
                public_key_content=None,
                remove_key=key["public_key_path"],
            )
            messages.append("Removed from server")
        except Exception as e:
            messages.append(f"Failed to remove from server: {e}")

    # Mark as revoked in DB
    database.revoke_key(conn, key_id)

    # Delete local key files
    for path_str in [key["public_key_path"], key["private_key_path"]]:
        p = Path(path_str)
        if p.exists():
            p.unlink()
            messages.append(f"Deleted: {p.name}")

    database.delete_key(conn, key_id)
    return True, "; ".join(messages)


def cleanup_expired_keys(data_dir: Path, conn, ssh_deploy_func=None) -> list[str]:
    """Find and clean up all expired keys. Returns list of actions taken."""
    expired = database.get_expired_keys(conn)
    results = []

    for key in expired:
        ok, msg = revoke_key(data_dir, conn, key["id"], ssh_deploy_func)
        status = "OK" if ok else "FAIL"
        results.append(f"[{status}] {key['key_name']} ({key['server_host']}): {msg}")

    return results


def get_private_key_content(private_key_path: str) -> str:
    """Read private key content for sharing with Claude."""
    return Path(private_key_path).read_text(encoding="utf-8")


def get_public_key_content(public_key_path: str) -> str:
    """Read public key content."""
    return Path(public_key_path).read_text(encoding="utf-8").strip()


def is_key_expired(key: dict) -> bool:
    """Check if a key has expired."""
    expires = key.get("expires_at", "")
    if not expires:
        return False
    try:
        exp_dt = datetime.fromisoformat(expires)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp_dt
    except (ValueError, TypeError):
        return False


def format_remaining_time(expires_at: str, lang: str = "en") -> str:
    """Format remaining time until expiry."""
    try:
        from . import i18n

        exp_dt = datetime.fromisoformat(expires_at)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        delta = exp_dt - datetime.now(timezone.utc)
        if delta.total_seconds() <= 0:
            return i18n.t("keys.status_expired")
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        if hours > 0:
            return i18n.t("keys.remaining", h=hours, m=minutes)
        return i18n.t("keys.remaining_min", m=minutes)
    except (ValueError, TypeError):
        return "Unknown"
