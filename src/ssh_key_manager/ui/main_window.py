"""Main application window with left navigation and right content area."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Callable

from .. import __version__
from .. import config as app_config
from .. import database
from .. import permissions
from .. import key_manager
from .. import ssh_deploy
from .. import clipboard
from .. import share


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"SSH Key Manager v{__version__}")
        self.geometry("960x640")
        self.minsize(800, 500)

        # State
        self._app_dir: Path = app_config.get_app_dir()
        self._data_dir: Path | None = None
        self._conn = None

        # Initialize data directory
        self._init_data_dir()

        # Apply theme
        self._apply_theme()

        # Build UI
        self._build_ui()

        # Load initial data
        self._refresh_all()

    def _apply_theme(self):
        style = ttk.Style(self)
        available = style.theme_names()
        for theme in ("clam", "alt", "default"):
            if theme in available:
                style.theme_use(theme)
                break

        style.configure("Nav.TButton", padding=(12, 8), font=("system", 11))
        style.configure("Active.TButton", padding=(12, 8), font=("system", 11, "bold"))
        style.configure("Action.TButton", padding=(8, 4), font=("system", 10))
        style.configure("Danger.TButton", padding=(8, 4), font=("system", 10))

    def _init_data_dir(self):
        data_dir = app_config.get_data_dir_path(self._app_dir)
        if data_dir is None:
            data_dir = self._prompt_data_dir()
            if data_dir is None:
                self.destroy()
                return
        self._data_dir = data_dir
        app_config.init_data_dir(self._data_dir)

        # Ensure permissions
        keys_dir = self._data_dir / app_config.KEYS_DIR
        permissions.ensure_permissions(self._data_dir, keys_dir)

        # Connect to database
        self._conn = database.connect(self._data_dir)

        # Cleanup expired keys on startup
        self._cleanup_expired()

    def _prompt_data_dir(self) -> Path | None:
        result = messagebox.askyesno(
            "Welcome",
            "This is your first time running SSH Key Manager.\n\n"
            "Please choose a directory to store your SSH keys and configuration.\n"
            "You can place this directory in OneDrive or a USB drive for cross-device sync.\n\n"
            "Continue?",
        )
        if not result:
            return None

        path = filedialog.askdirectory(title="Choose Data Directory")
        if not path:
            return None

        data_dir = Path(path) / "ssh-key-manager-data"
        app_config.set_data_dir_path(self._app_dir, data_dir)
        return data_dir

    def _build_ui(self):
        # Main container
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # Left navigation
        nav = ttk.Frame(main, width=180)
        nav.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        nav.pack_propagate(False)

        # Version label
        ttk.Label(nav, text=f"SSH Key Manager", font=("system", 12, "bold")).pack(pady=(8, 2))
        ttk.Label(nav, text=f"v{__version__}", font=("system", 9)).pack(pady=(0, 16))

        # Nav buttons
        self._nav_keys_btn = ttk.Button(
            nav, text="  Key Management", style="Active.TButton",
            command=lambda: self._switch_page("keys")
        )
        self._nav_keys_btn.pack(fill=tk.X, pady=2)

        self._nav_servers_btn = ttk.Button(
            nav, text="  Server Management", style="Nav.TButton",
            command=lambda: self._switch_page("servers")
        )
        self._nav_servers_btn.pack(fill=tk.X, pady=2)

        ttk.Separator(nav, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        # Settings button
        ttk.Button(
            nav, text="  Data Directory", style="Nav.TButton",
            command=self._change_data_dir
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            nav, text="  Cleanup Expired", style="Nav.TButton",
            command=self._manual_cleanup
        ).pack(fill=tk.X, pady=2)

        # Right content area
        self._content = ttk.Frame(main)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Pages
        self._pages = {}
        self._build_keys_page()
        self._build_servers_page()

        # Show keys page by default
        self._switch_page("keys")

    def _switch_page(self, page: str):
        for p in self._pages.values():
            p.pack_forget()
        self._pages[page].pack(fill=tk.BOTH, expand=True)

        self._nav_keys_btn.configure(
            style="Active.TButton" if page == "keys" else "Nav.TButton"
        )
        self._nav_servers_btn.configure(
            style="Active.TButton" if page == "servers" else "Nav.TButton"
        )

    def _build_keys_page(self):
        page = ttk.Frame(self._content)
        self._pages["keys"] = page

        # Title
        ttk.Label(page, text="SSH Key Management", font=("system", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))

        # Generate key section
        gen_frame = ttk.LabelFrame(page, text="Generate New Key", padding=8)
        gen_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(gen_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Server:").pack(side=tk.LEFT)
        self._key_server_var = tk.StringVar()
        self._key_server_combo = ttk.Combobox(row1, textvariable=self._key_server_var, state="readonly", width=30)
        self._key_server_combo.pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(row1, text="Duration:").pack(side=tk.LEFT)
        self._key_duration_var = tk.StringVar(value="1 hour")
        durations = [f"{h} hour{'s' if h > 1 else ''}" for h in app_config.VALID_DURATIONS]
        ttk.Combobox(
            row1, textvariable=self._key_duration_var, values=durations,
            state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(row1, text="Label:").pack(side=tk.LEFT)
        self._key_label_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._key_label_var, width=20).pack(side=tk.LEFT, padx=(4, 8))

        row2 = ttk.Frame(gen_frame)
        row2.pack(fill=tk.X, pady=(4, 0))

        ttk.Label(row2, text="Server Password (for key deployment):").pack(side=tk.LEFT)
        self._key_password_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._key_password_var, show="*", width=20).pack(side=tk.LEFT, padx=(4, 8))

        ttk.Button(row2, text="Generate & Deploy", style="Action.TButton", command=self._generate_key).pack(side=tk.RIGHT)

        # Key list
        list_frame = ttk.LabelFrame(page, text="Active Keys", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "server", "duration", "expires", "status")
        self._keys_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self._keys_tree.heading("name", text="Key Name")
        self._keys_tree.heading("server", text="Server")
        self._keys_tree.heading("duration", text="Duration")
        self._keys_tree.heading("expires", text="Expires In")
        self._keys_tree.heading("status", text="Status")
        self._keys_tree.column("name", width=150)
        self._keys_tree.column("server", width=180)
        self._keys_tree.column("duration", width=80)
        self._keys_tree.column("expires", width=120)
        self._keys_tree.column("status", width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._keys_tree.yview)
        self._keys_tree.configure(yscrollcommand=scrollbar.set)
        self._keys_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        btn_frame = ttk.Frame(page)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self._btn_share = ttk.Button(btn_frame, text="Share for Claude", style="Action.TButton", command=self._share_key, state=tk.DISABLED)
        self._btn_share.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_revoke = ttk.Button(btn_frame, text="Revoke Key", style="Danger.TButton", command=self._revoke_key, state=tk.DISABLED)
        self._btn_revoke.pack(side=tk.LEFT)

        self._keys_tree.bind("<<TreeviewSelect>>", self._on_key_select)

    def _build_servers_page(self):
        page = ttk.Frame(self._content)
        self._pages["servers"] = page

        ttk.Label(page, text="Server Management", font=("system", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))

        # Add server section
        add_frame = ttk.LabelFrame(page, text="Add Server", padding=8)
        add_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(add_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Name:").pack(side=tk.LEFT)
        self._srv_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._srv_name_var, width=15).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(row1, text="Host:").pack(side=tk.LEFT)
        self._srv_host_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._srv_host_var, width=20).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(row1, text="Port:").pack(side=tk.LEFT)
        self._srv_port_var = tk.StringVar(value="22")
        ttk.Entry(row1, textvariable=self._srv_port_var, width=6).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(row1, text="Username:").pack(side=tk.LEFT)
        self._srv_user_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._srv_user_var, width=12).pack(side=tk.LEFT, padx=(4, 8))

        row2 = ttk.Frame(add_frame)
        row2.pack(fill=tk.X, pady=(4, 0))

        ttk.Label(row2, text="Password:").pack(side=tk.LEFT)
        self._srv_pass_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._srv_pass_var, show="*", width=15).pack(side=tk.LEFT, padx=(4, 8))

        ttk.Button(row2, text="Test Connection", style="Action.TButton", command=self._test_server).pack(side=tk.LEFT, padx=8)
        ttk.Button(row2, text="Add Server", style="Action.TButton", command=self._add_server).pack(side=tk.RIGHT)

        # Server list
        list_frame = ttk.LabelFrame(page, text="Saved Servers", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "host", "port", "username")
        self._servers_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self._servers_tree.heading("name", text="Name")
        self._servers_tree.heading("host", text="Host")
        self._servers_tree.heading("port", text="Port")
        self._servers_tree.heading("username", text="Username")
        self._servers_tree.column("name", width=150)
        self._servers_tree.column("host", width=200)
        self._servers_tree.column("port", width=80)
        self._servers_tree.column("username", width=120)

        srv_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._servers_tree.yview)
        self._servers_tree.configure(yscrollcommand=srv_scrollbar.set)
        self._servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        srv_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(page)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self._btn_del_server = ttk.Button(
            btn_frame, text="Delete Server", style="Danger.TButton",
            command=self._delete_server, state=tk.DISABLED
        )
        self._btn_del_server.pack(side=tk.LEFT)

        self._servers_tree.bind("<<TreeviewSelect>>", self._on_server_select)

    # --- Data operations ---

    def _refresh_all(self):
        self._refresh_keys()
        self._refresh_servers()
        self._refresh_server_combo()

    def _refresh_keys(self):
        for item in self._keys_tree.get_children():
            self._keys_tree.delete(item)

        if not self._conn:
            return

        keys = database.list_keys(self._conn)
        for k in keys:
            remaining = key_manager.format_remaining_time(k["expires_at"])
            expired = key_manager.is_key_expired(k)
            status = "Expired" if expired else "Active"
            self._keys_tree.insert("", tk.END, iid=str(k["id"]), values=(
                k["key_name"],
                f"{k['server_username']}@{k['server_host']}",
                f"{k['duration_hours']}h",
                remaining,
                status,
            ))

    def _refresh_servers(self):
        for item in self._servers_tree.get_children():
            self._servers_tree.delete(item)

        if not self._conn:
            return

        servers = database.list_servers(self._conn)
        for s in servers:
            self._servers_tree.insert("", tk.END, iid=str(s["id"]), values=(
                s["name"], s["host"], s["port"], s["username"]
            ))

    def _refresh_server_combo(self):
        if not self._conn:
            return
        servers = database.list_servers(self._conn)
        values = [f"{s['name']} ({s['username']}@{s['host']})" for s in servers]
        self._key_server_combo["values"] = values
        if values:
            self._key_server_combo.current(0)

    def _get_selected_key(self) -> dict | None:
        sel = self._keys_tree.selection()
        if not sel:
            return None
        return database.get_key(self._conn, int(sel[0]))

    def _get_selected_server(self) -> dict | None:
        sel = self._servers_tree.selection()
        if not sel:
            return None
        return database.get_server(self._conn, int(sel[0]))

    def _get_selected_server_id(self) -> int | None:
        sel = self._key_server_combo.get()
        if not sel or not self._conn:
            return None
        servers = database.list_servers(self._conn)
        for s in servers:
            combo_str = f"{s['name']} ({s['username']}@{s['host']})"
            if combo_str == sel:
                return s["id"]
        return None

    # --- Key actions ---

    def _generate_key(self):
        server_id = self._get_selected_server_id()
        if server_id is None:
            messagebox.showwarning("Warning", "Please select a server")
            return

        dur_str = self._key_duration_var.get()
        hours = int(dur_str.split()[0])
        label = self._key_label_var.get().strip()

        try:
            key = key_manager.generate_key(
                self._data_dir, self._conn, server_id, hours, label
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate key: {e}")
            return

        # Deploy public key
        password = self._srv_pass_var.get() or self._key_password_var.get() or None
        server = database.get_server(self._conn, server_id)
        if server:
            try:
                ssh_deploy.deploy_public_key(
                    host=server["host"],
                    username=server["username"],
                    port=server["port"],
                    public_key_path=key["public_key_path"],
                    password=password,
                )
                messagebox.showinfo("Success", f"Key generated and deployed to {server['host']}")
            except Exception as e:
                messagebox.showwarning(
                    "Partial Success",
                    f"Key generated but deployment failed:\n{e}\n\nYou can deploy manually later."
                )

        self._key_label_var.set("")
        self._refresh_keys()

    def _share_key(self):
        key = self._get_selected_key()
        if not key:
            return

        content = share.generate_claude_share(key)
        if clipboard.copy_to_clipboard(content):
            messagebox.showinfo("Copied", "Claude-compatible key info copied to clipboard!")
        else:
            # Show in a text window as fallback
            win = tk.Toplevel(self)
            win.title("Share Content")
            win.geometry("600x400")
            text = tk.Text(win, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            text.insert("1.0", content)
            text.configure(state=tk.NORMAL)

    def _revoke_key(self):
        key = self._get_selected_key()
        if not key:
            return

        if not messagebox.askyesno(
            "Confirm Revoke",
            f"Are you sure you want to revoke key '{key['key_name']}'?\n\n"
            f"This will remove the key from {key['server_host']} and delete local files.",
        ):
            return

        password = self._key_password_var.get() or None

        def deploy_remove(**kwargs):
            return ssh_deploy.remove_public_key(
                host=key["server_host"],
                username=key["server_username"],
                port=22,
                public_key_path=key["public_key_path"],
                password=password,
            )

        ok, msg = key_manager.revoke_key(self._data_dir, self._conn, key["id"], deploy_remove)
        if ok:
            messagebox.showinfo("Revoked", msg)
        else:
            messagebox.showwarning("Warning", msg)
        self._refresh_keys()
        self._btn_share.configure(state=tk.DISABLED)
        self._btn_revoke.configure(state=tk.DISABLED)

    def _on_key_select(self, _event):
        has_sel = bool(self._keys_tree.selection())
        self._btn_share.configure(state=tk.NORMAL if has_sel else tk.DISABLED)
        self._btn_revoke.configure(state=tk.NORMAL if has_sel else tk.DISABLED)

    # --- Server actions ---

    def _add_server(self):
        name = self._srv_name_var.get().strip()
        host = self._srv_host_var.get().strip()
        port_str = self._srv_port_var.get().strip()
        username = self._srv_user_var.get().strip()

        if not all([name, host, username]):
            messagebox.showwarning("Warning", "Name, Host, and Username are required")
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning("Warning", "Invalid port number")
            return

        database.add_server(self._conn, name, host, port, username)
        messagebox.showinfo("Success", f"Server '{name}' added")

        self._srv_name_var.set("")
        self._srv_host_var.set("")
        self._srv_port_var.set("22")
        self._srv_user_var.set("")

        self._refresh_servers()
        self._refresh_server_combo()

    def _delete_server(self):
        server = self._get_selected_server()
        if not server:
            return

        # Check for active keys
        keys = database.list_keys(self._conn)
        active_keys = [k for k in keys if k["server_id"] == server["id"]]

        msg = f"Are you sure you want to delete server '{server['name']}'?"
        if active_keys:
            msg += f"\n\nWarning: This server has {len(active_keys)} active key(s) that will also be deleted."

        if not messagebox.askyesno("Confirm Delete", msg):
            return

        # Revoke and delete associated keys
        for k in active_keys:
            key_manager.revoke_key(self._data_dir, self._conn, k["id"])

        database.delete_server(self._conn, server["id"])
        messagebox.showinfo("Deleted", f"Server '{server['name']}' deleted")
        self._refresh_all()

    def _test_server(self):
        host = self._srv_host_var.get().strip()
        username = self._srv_user_var.get().strip()
        port_str = self._srv_port_var.get().strip()
        password = self._srv_pass_var.get() or None

        if not all([host, username]):
            messagebox.showwarning("Warning", "Host and Username are required")
            return

        try:
            port = int(port_str)
        except ValueError:
            port = 22

        ok, msg = ssh_deploy.test_connection(host, username, port, password)
        if ok:
            messagebox.showinfo("Connection Test", "Connection successful!")
        else:
            messagebox.showerror("Connection Test", f"Connection failed:\n{msg}")

    def _on_server_select(self, _event):
        has_sel = bool(self._servers_tree.selection())
        self._btn_del_server.configure(state=tk.NORMAL if has_sel else tk.DISABLED)

    # --- Utility actions ---

    def _change_data_dir(self):
        path = filedialog.askdirectory(title="Choose New Data Directory")
        if not path:
            return

        new_dir = Path(path) / "ssh-key-manager-data"
        if not messagebox.askyesno(
            "Confirm",
            f"Change data directory to:\n{new_dir}\n\n"
            "The application will restart to apply the change."
        ):
            return

        app_config.set_data_dir_path(self._app_dir, new_dir)
        self.destroy()

    def _manual_cleanup(self):
        results = self._cleanup_expired()
        if results:
            messagebox.showinfo("Cleanup", "\n".join(results))
        else:
            messagebox.showinfo("Cleanup", "No expired keys to clean up.")
        self._refresh_keys()

    def _cleanup_expired(self) -> list[str]:
        if not self._conn:
            return []
        return key_manager.cleanup_expired_keys(self._data_dir, self._conn)

    def destroy(self):
        if self._conn:
            self._conn.close()
        super().destroy()
