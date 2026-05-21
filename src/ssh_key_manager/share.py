"""Generate formatted share content for Claude Code."""

from __future__ import annotations

from . import key_manager


def generate_claude_share(key: dict) -> str:
    """Generate formatted content for sharing SSH key info with Claude Code."""
    private_key = key_manager.get_private_key_content(key["private_key_path"])
    public_key = key_manager.get_public_key_content(key["public_key_path"])
    remaining = key_manager.format_remaining_time(key["expires_at"])

    return (
        f"# SSH Key for {key['server_username']}@{key['server_host']}\n\n"
        f"## Connection Info\n"
        f"- Host: `{key['server_host']}`\n"
        f"- User: `{key['server_username']}`\n"
        f"- Key: `{key['private_key_path']}`\n"
        f"- Expires: {remaining}\n\n"
        f"## Private Key\n"
        f"Save to a file and use as identity file:\n\n"
        f"```\n{private_key}```\n\n"
        f"## Quick Connect\n"
        f"```bash\n"
        f"ssh -i <key-file> {key['server_username']}@{key['server_host']}\n"
        f"```\n\n"
        f"## Public Key (for reference)\n"
        f"```\n{public_key}\n```\n"
    )
