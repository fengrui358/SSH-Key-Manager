"""SSH public key deployment to remote servers via paramiko."""

from __future__ import annotations

from pathlib import Path

import paramiko


def _connect(
    host: str,
    username: str,
    port: int,
    password: str | None = None,
    key_path: str | None = None,
    key_passphrase: str | None = None,
) -> paramiko.SSHClient:
    """Create and return a connected SSH client."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict = {
        "hostname": host,
        "port": port,
        "username": username,
        "timeout": 15,
    }

    if key_path:
        connect_kwargs["key_filename"] = key_path
        if key_passphrase:
            connect_kwargs["passphrase"] = key_passphrase
    elif password:
        connect_kwargs["password"] = password

    client.connect(**connect_kwargs)
    return client


def deploy_public_key(
    host: str,
    username: str,
    port: int,
    public_key_content: str | None = None,
    public_key_path: str | None = None,
    password: str | None = None,
    key_path: str | None = None,
    key_passphrase: str | None = None,
) -> str:
    """Deploy a public key on a remote server's authorized_keys."""
    if public_key_content is None and public_key_path:
        public_key_content = Path(public_key_path).read_text(encoding="utf-8").strip()

    if not public_key_content:
        raise ValueError("No public key content provided")

    client = _connect(host, username, port, password, key_path, key_passphrase)
    try:
        _add_to_authorized_keys(client, public_key_content)
        return "Public key deployed successfully"
    finally:
        client.close()


def remove_public_key(
    host: str,
    username: str,
    port: int,
    public_key_path: str,
    password: str | None = None,
    key_path: str | None = None,
    key_passphrase: str | None = None,
) -> str:
    """Remove a public key from a remote server's authorized_keys."""
    pub_content = Path(public_key_path).read_text(encoding="utf-8").strip()

    client = _connect(host, username, port, password, key_path, key_passphrase)
    try:
        _remove_from_authorized_keys(client, pub_content)
        return "Public key removed from server"
    finally:
        client.close()


def test_connection(
    host: str,
    username: str,
    port: int,
    password: str | None = None,
    key_path: str | None = None,
    key_passphrase: str | None = None,
) -> tuple[bool, str]:
    """Test SSH connection to a server."""
    try:
        client = _connect(host, username, port, password, key_path, key_passphrase)
        client.close()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def _add_to_authorized_keys(client: paramiko.SSHClient, pub_key: str) -> None:
    cmd = (
        f'mkdir -p ~/.ssh && '
        f'grep -qF "{pub_key}" ~/.ssh/authorized_keys 2>/dev/null || '
        f'echo "{pub_key}" >> ~/.ssh/authorized_keys && '
        f'chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys'
    )
    _, stdout, stderr = client.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"Failed to deploy key: {stderr.read().decode()}")


def _remove_from_authorized_keys(client: paramiko.SSHClient, pub_key: str) -> None:
    key_part = pub_key.split()[:2]
    key_pattern = " ".join(key_part) if len(key_part) >= 2 else pub_key
    cmd = (
        f'temp_file=$(mktemp) && '
        f'grep -vF "{key_pattern}" ~/.ssh/authorized_keys > "$temp_file" 2>/dev/null && '
        f'mv "$temp_file" ~/.ssh/authorized_keys && '
        f'chmod 600 ~/.ssh/authorized_keys; '
        f'rm -f "$temp_file"'
    )
    _, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
