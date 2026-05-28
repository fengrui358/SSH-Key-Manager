"""Internationalization support for English and Chinese."""

from __future__ import annotations

from .config import load_config, save_config

LANGUAGES = {"en": "English", "zh": "中文"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # App
        "app.title": "SSH Key Manager",
        "app.version": "v{version}",
        # Nav
        "nav.keys": "Key Management",
        "nav.servers": "Server Management",
        "nav.data_dir": "Data Directory",
        "nav.cleanup": "Cleanup Expired",
        "nav.language": "Language",
        # Keys page
        "keys.title": "SSH Key Management",
        "keys.generate": "Generate New Key",
        "keys.server": "Server:",
        "keys.duration": "Duration:",
        "keys.label": "Label:",
        "keys.password": "Deploy Password:",
        "keys.btn_generate": "Generate & Deploy",
        "keys.active_keys": "Active Keys",
        "keys.col_name": "Key Name",
        "keys.col_server": "Server",
        "keys.col_duration": "Duration",
        "keys.col_expires": "Expires In",
        "keys.col_status": "Status",
        "keys.btn_share": "Share for Claude",
        "keys.btn_revoke": "Revoke Key",
        "keys.btn_export": "Export Key",
        "keys.btn_open_location": "Open Location",
        "keys.menu_open_location": "Show in File Manager",
        "keys.status_active": "Active",
        "keys.status_expired": "Expired",
        "keys.hour": "{h} hour",
        "keys.hours": "{h} hours",
        "keys.days": "{d} days",
        "keys.permanent": "Permanent",
        "keys.remaining": "{h}h {m}m remaining",
        "keys.remaining_min": "{m}m remaining",
        "keys.remaining_permanent": "Permanent",
        # Servers page
        "servers.title": "Server Management",
        "servers.add": "Add Server",
        "servers.name": "Name:",
        "servers.host": "Host:",
        "servers.port": "Port:",
        "servers.username": "Username:",
        "servers.auth_type": "Auth:",
        "servers.auth_password": "Password",
        "servers.auth_key": "Private Key",
        "servers.password": "Password:",
        "servers.key_file": "Key File:",
        "servers.key_select": "Select Key",
        "servers.key_passphrase": "Passphrase:",
        "servers.btn_test": "Test Connection",
        "servers.btn_add": "Add Server",
        "servers.saved": "Saved Servers",
        "servers.col_name": "Name",
        "servers.col_host": "Host",
        "servers.col_port": "Port",
        "servers.col_username": "Username",
        "servers.col_auth": "Auth",
        "servers.btn_delete": "Delete Server",
        "servers.btn_edit": "Edit Server",
        "servers.btn_revoke_all": "Revoke All Keys",
        "servers.btn_cancel_edit": "Cancel",
        # Dialogs
        "dialog.welcome_title": "Welcome",
        "dialog.welcome_msg": (
            "This is your first time running SSH Key Manager.\n\n"
            "Please choose a directory to store your SSH keys and configuration.\n"
            "You can place this directory in OneDrive or a USB drive for cross-device sync.\n\n"
            "Continue?"
        ),
        "dialog.choose_data_dir": "Choose Data Directory",
        "dialog.confirm_revoke_title": "Confirm Revoke",
        "dialog.confirm_revoke": (
            "Are you sure you want to revoke key '{name}'?\n\n"
            "This will remove the key from {host} and delete local files."
        ),
        "dialog.confirm_revoke_all_title": "Confirm Revoke All",
        "dialog.confirm_revoke_all": (
            "Are you sure you want to revoke all {count} key(s) for server '{name}'?\n\n"
            "This will remove all keys from {host} and delete local files."
        ),
        "dialog.confirm_delete_title": "Confirm Delete",
        "dialog.confirm_delete": "Are you sure you want to delete server '{name}'?",
        "dialog.confirm_delete_keys": (
            "\n\nWarning: This server has {count} active key(s) that will also be deleted."
        ),
        "dialog.confirm_data_dir": (
            "Change data directory to:\n{path}\n\n"
            "The application will restart to apply the change."
        ),
        "dialog.confirm": "Confirm",
        "dialog.success": "Success",
        "dialog.warning": "Warning",
        "dialog.error": "Error",
        "dialog.info": "Info",
        "dialog.copied": "Copied",
        "dialog.copied_msg": "Claude-compatible key info copied to clipboard!",
        "dialog.share_title": "Share Content",
        # Messages
        "msg.select_server": "Please select a server",
        "msg.key_generated": "Key generated and deployed to {host}",
        "msg.key_gen_partial": "Key generated but deployment failed:\n{error}\n\nYou can deploy manually later.",
        "msg.key_gen_error": "Failed to generate key: {error}",
        "msg.server_added": "Server '{name}' added",
        "msg.server_deleted": "Server '{name}' deleted",
        "msg.fields_required": "Name, Host, and Username are required",
        "msg.invalid_port": "Invalid port number",
        "msg.conn_ok": "Connection successful!",
        "msg.conn_fail": "Connection failed:\n{error}",
        "msg.no_expired": "No expired keys to clean up.",
        "msg.cleanup_done": "Cleaned up {count} expired key(s).",
        "msg.revoked": "{message}",
        "msg.select_key_file": "Select SSH Private Key",
        "msg.keyfile_all": "All Files",
        "msg.server_updated": "Server '{name}' updated",
        "msg.export_title": "Export Private Key",
        "msg.export_success": "Private key exported to:\n{path}",
        "msg.export_fail": "Export failed: {error}",
        "msg.key_file_not_found": "Private key file not found. It may have been moved or deleted.",
        "msg.no_keys_to_revoke": "No active keys to revoke for this server.",
        "msg.all_keys_revoked": "Revoked {count} key(s) from server '{name}'.",
    },
    "zh": {
        # App
        "app.title": "SSH 密钥管理器",
        "app.version": "v{version}",
        # Nav
        "nav.keys": "密钥管理",
        "nav.servers": "服务器管理",
        "nav.data_dir": "数据目录",
        "nav.cleanup": "清理过期密钥",
        "nav.language": "语言",
        # Keys page
        "keys.title": "SSH 密钥管理",
        "keys.generate": "生成新密钥",
        "keys.server": "服务器：",
        "keys.duration": "有效期：",
        "keys.label": "标签：",
        "keys.password": "部署密码：",
        "keys.btn_generate": "生成并部署",
        "keys.active_keys": "活动密钥",
        "keys.col_name": "密钥名称",
        "keys.col_server": "服务器",
        "keys.col_duration": "有效期",
        "keys.col_expires": "剩余时间",
        "keys.col_status": "状态",
        "keys.btn_share": "分享给 Claude",
        "keys.btn_revoke": "撤销密钥",
        "keys.btn_export": "导出密钥",
        "keys.btn_open_location": "打开位置",
        "keys.menu_open_location": "在文件管理器中显示",
        "keys.status_active": "有效",
        "keys.status_expired": "已过期",
        "keys.hour": "{h} 小时",
        "keys.hours": "{h} 小时",
        "keys.days": "{d} 天",
        "keys.permanent": "长期",
        "keys.remaining": "剩余 {h}小时 {m}分钟",
        "keys.remaining_min": "剩余 {m}分钟",
        "keys.remaining_permanent": "长期有效",
        # Servers page
        "servers.title": "服务器管理",
        "servers.add": "添加服务器",
        "servers.name": "名称：",
        "servers.host": "主机：",
        "servers.port": "端口：",
        "servers.username": "用户名：",
        "servers.auth_type": "认证方式：",
        "servers.auth_password": "密码",
        "servers.auth_key": "私钥",
        "servers.password": "密码：",
        "servers.key_file": "密钥文件：",
        "servers.key_select": "选择密钥",
        "servers.key_passphrase": "密钥口令：",
        "servers.btn_test": "测试连接",
        "servers.btn_add": "添加服务器",
        "servers.saved": "已保存的服务器",
        "servers.col_name": "名称",
        "servers.col_host": "主机",
        "servers.col_port": "端口",
        "servers.col_username": "用户名",
        "servers.col_auth": "认证",
        "servers.btn_delete": "删除服务器",
        "servers.btn_edit": "编辑服务器",
        "servers.btn_revoke_all": "撤回全部密钥",
        "servers.btn_cancel_edit": "取消",
        # Dialogs
        "dialog.welcome_title": "欢迎",
        "dialog.welcome_msg": (
            "这是您首次运行 SSH 密钥管理器。\n\n"
            "请选择一个目录来存储 SSH 密钥和配置。\n"
            "您可以将此目录放在 OneDrive 或 U 盘中实现跨设备同步。\n\n"
            "继续？"
        ),
        "dialog.choose_data_dir": "选择数据目录",
        "dialog.confirm_revoke_title": "确认撤销",
        "dialog.confirm_revoke": (
            "确定要撤销密钥「{name}」吗？\n\n"
            "将从 {host} 移除公钥并删除本地文件。"
        ),
        "dialog.confirm_revoke_all_title": "确认撤回全部",
        "dialog.confirm_revoke_all": (
            "确定要撤回服务器「{name}」的全部 {count} 个密钥吗？\n\n"
            "将从 {host} 移除所有公钥并删除本地文件。"
        ),
        "dialog.confirm_delete_title": "确认删除",
        "dialog.confirm_delete": "确定要删除服务器「{name}」吗？",
        "dialog.confirm_delete_keys": (
            "\n\n警告：该服务器有 {count} 个活动密钥也将被删除。"
        ),
        "dialog.confirm_data_dir": (
            "将数据目录更改为：\n{path}\n\n"
            "应用程序将重启以应用更改。"
        ),
        "dialog.confirm": "确认",
        "dialog.success": "成功",
        "dialog.warning": "警告",
        "dialog.error": "错误",
        "dialog.info": "提示",
        "dialog.copied": "已复制",
        "dialog.copied_msg": "Claude 格式的密钥信息已复制到剪贴板！",
        "dialog.share_title": "分享内容",
        # Messages
        "msg.select_server": "请选择一个服务器",
        "msg.key_generated": "密钥已生成并部署到 {host}",
        "msg.key_gen_partial": "密钥已生成但部署失败：\n{error}\n\n您可以稍后手动部署。",
        "msg.key_gen_error": "生成密钥失败：{error}",
        "msg.server_added": "服务器「{name}」已添加",
        "msg.server_deleted": "服务器「{name}」已删除",
        "msg.fields_required": "名称、主机和用户名为必填项",
        "msg.invalid_port": "无效的端口号",
        "msg.conn_ok": "连接成功！",
        "msg.conn_fail": "连接失败：\n{error}",
        "msg.no_expired": "没有需要清理的过期密钥。",
        "msg.cleanup_done": "已清理 {count} 个过期密钥。",
        "msg.revoked": "{message}",
        "msg.select_key_file": "选择 SSH 私钥文件",
        "msg.keyfile_all": "所有文件",
        "msg.server_updated": "服务器「{name}」已更新",
        "msg.export_title": "导出私钥",
        "msg.export_success": "私钥已导出到：\n{path}",
        "msg.export_fail": "导出失败：{error}",
        "msg.key_file_not_found": "私钥文件未找到，可能已被移动或删除。",
        "msg.no_keys_to_revoke": "该服务器没有可撤回的活动密钥。",
        "msg.all_keys_revoked": "已从服务器「{name}」撤回 {count} 个密钥。",
    },
}

_current_lang = "en"


def get_lang() -> str:
    return _current_lang


def set_lang(lang: str) -> None:
    global _current_lang
    _current_lang = lang


def load_lang(config: dict) -> None:
    global _current_lang
    _current_lang = config.get("language", "en")


def t(key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(_current_lang, {}).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
