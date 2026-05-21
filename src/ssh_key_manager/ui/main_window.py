"""Main application window with left navigation and right content area."""

from __future__ import annotations

import shutil
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .. import __version__
from .. import config as app_config
from .. import database
from .. import i18n
from .. import permissions
from .. import key_manager
from .. import ssh_deploy
from .. import clipboard
from .. import share


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._app_dir: Path = app_config.get_app_dir()
        self._data_dir: Path | None = None
        self._conn = None
        self._config: dict = {}

        # Initialize data directory
        self._init_data_dir()

        # Load language from config
        i18n.load_lang(self._config)

        self.title(f"{i18n.t('app.title')} v{__version__}")
        self.geometry("960x640")
        self.minsize(800, 500)

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

        # Load config
        self._config = app_config.load_config(self._data_dir)

        # Ensure permissions
        keys_dir = self._data_dir / app_config.KEYS_DIR
        permissions.ensure_permissions(self._data_dir, keys_dir)

        # Connect to database
        self._conn = database.connect(self._data_dir)

        # Cleanup expired keys on startup
        self._cleanup_expired()

    def _prompt_data_dir(self) -> Path | None:
        result = messagebox.askyesno(
            i18n.t("dialog.welcome_title"),
            i18n.t("dialog.welcome_msg"),
        )
        if not result:
            return None

        path = filedialog.askdirectory(title=i18n.t("dialog.choose_data_dir"))
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
        ttk.Label(nav, text="SSH Key Manager", font=("system", 12, "bold")).pack(pady=(8, 2))
        ttk.Label(nav, text=f"v{__version__}", font=("system", 9)).pack(pady=(0, 16))

        # Nav buttons
        self._nav_keys_btn = ttk.Button(
            nav, text=f"  {i18n.t('nav.keys')}", style="Active.TButton",
            command=lambda: self._switch_page("keys")
        )
        self._nav_keys_btn.pack(fill=tk.X, pady=2)

        self._nav_servers_btn = ttk.Button(
            nav, text=f"  {i18n.t('nav.servers')}", style="Nav.TButton",
            command=lambda: self._switch_page("servers")
        )
        self._nav_servers_btn.pack(fill=tk.X, pady=2)

        ttk.Separator(nav, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        ttk.Button(
            nav, text=f"  {i18n.t('nav.data_dir')}", style="Nav.TButton",
            command=self._change_data_dir
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            nav, text=f"  {i18n.t('nav.cleanup')}", style="Nav.TButton",
            command=self._manual_cleanup
        ).pack(fill=tk.X, pady=2)

        ttk.Separator(nav, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        # Language switcher
        self._lang_var = tk.StringVar(value=i18n.get_lang())
        for code, name in i18n.LANGUAGES.items():
            ttk.Radiobutton(
                nav, text=name, value=code, variable=self._lang_var,
                command=self._change_language
            ).pack(anchor=tk.W, padx=16)

        # Right content area
        self._content = ttk.Frame(main)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Pages
        self._pages = {}
        self._build_keys_page()
        self._build_servers_page()

        # Show keys page by default
        self._switch_page("keys")

    def _change_language(self):
        lang = self._lang_var.get()
        i18n.set_lang(lang)
        self._config["language"] = lang
        app_config.save_config(self._data_dir, self._config)
        self.destroy()

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
        ttk.Label(page, text=i18n.t("keys.title"), font=("system", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))

        # Generate key section
        gen_frame = ttk.LabelFrame(page, text=i18n.t("keys.generate"), padding=8)
        gen_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(gen_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text=i18n.t("keys.server")).pack(side=tk.LEFT)
        self._key_server_var = tk.StringVar()
        self._key_server_combo = ttk.Combobox(row1, textvariable=self._key_server_var, state="readonly", width=30)
        self._key_server_combo.pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(row1, text=i18n.t("keys.duration")).pack(side=tk.LEFT)
        self._key_duration_var = tk.StringVar()
        self._key_duration_combo = ttk.Combobox(
            row1, textvariable=self._key_duration_var, state="readonly", width=12
        )
        self._key_duration_combo.pack(side=tk.LEFT, padx=(4, 16))

        row2 = ttk.Frame(gen_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text=i18n.t("keys.label")).pack(side=tk.LEFT)
        self._key_label_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._key_label_var, width=20).pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(row2, text=i18n.t("keys.password")).pack(side=tk.LEFT)
        self._key_password_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._key_password_var, show="*", width=20).pack(side=tk.LEFT, padx=(4, 8))

        ttk.Button(row2, text=i18n.t("keys.btn_generate"), style="Action.TButton", command=self._generate_key).pack(side=tk.RIGHT)

        # Key list
        list_frame = ttk.LabelFrame(page, text=i18n.t("keys.active_keys"), padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "server", "duration", "expires", "status")
        self._keys_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self._keys_tree.heading("name", text=i18n.t("keys.col_name"))
        self._keys_tree.heading("server", text=i18n.t("keys.col_server"))
        self._keys_tree.heading("duration", text=i18n.t("keys.col_duration"))
        self._keys_tree.heading("expires", text=i18n.t("keys.col_expires"))
        self._keys_tree.heading("status", text=i18n.t("keys.col_status"))
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

        self._btn_share = ttk.Button(
            btn_frame, text=i18n.t("keys.btn_share"), style="Action.TButton",
            command=self._share_key, state=tk.DISABLED
        )
        self._btn_share.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_revoke = ttk.Button(
            btn_frame, text=i18n.t("keys.btn_revoke"), style="Danger.TButton",
            command=self._revoke_key, state=tk.DISABLED
        )
        self._btn_revoke.pack(side=tk.LEFT)

        self._keys_tree.bind("<<TreeviewSelect>>", self._on_key_select)

    def _build_servers_page(self):
        page = ttk.Frame(self._content)
        self._pages["servers"] = page

        ttk.Label(page, text=i18n.t("servers.title"), font=("system", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))

        # Add server section
        add_frame = ttk.LabelFrame(page, text=i18n.t("servers.add"), padding=8)
        add_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(add_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text=i18n.t("servers.name")).pack(side=tk.LEFT)
        self._srv_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._srv_name_var, width=30).pack(side=tk.LEFT, padx=(4, 12), fill=tk.X, expand=True)

        row1b = ttk.Frame(add_frame)
        row1b.pack(fill=tk.X, pady=2)

        ttk.Label(row1b, text=i18n.t("servers.host")).pack(side=tk.LEFT)
        self._srv_host_var = tk.StringVar()
        ttk.Entry(row1b, textvariable=self._srv_host_var, width=22).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(row1b, text=i18n.t("servers.port")).pack(side=tk.LEFT)
        self._srv_port_var = tk.StringVar(value="22")
        ttk.Entry(row1b, textvariable=self._srv_port_var, width=6).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(row1b, text=i18n.t("servers.username")).pack(side=tk.LEFT)
        self._srv_user_var = tk.StringVar()
        ttk.Entry(row1b, textvariable=self._srv_user_var, width=12).pack(side=tk.LEFT, padx=(4, 8))

        # Auth type row
        row2 = ttk.Frame(add_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text=i18n.t("servers.auth_type")).pack(side=tk.LEFT)
        self._srv_auth_var = tk.StringVar(value="password")
        auth_combo = ttk.Combobox(
            row2, textvariable=self._srv_auth_var,
            values=["password", "key"], state="readonly", width=8
        )
        auth_combo.pack(side=tk.LEFT, padx=(4, 8))
        auth_combo.bind("<<ComboboxSelected>>", self._on_auth_type_change)

        # Password fields
        self._pwd_frame = ttk.Frame(add_frame)
        self._pwd_frame.pack(fill=tk.X, pady=2)

        ttk.Label(self._pwd_frame, text=i18n.t("servers.password")).pack(side=tk.LEFT)
        self._srv_pass_var = tk.StringVar()
        ttk.Entry(self._pwd_frame, textvariable=self._srv_pass_var, show="*", width=20).pack(side=tk.LEFT, padx=(4, 8))

        # Key fields (hidden by default)
        self._key_frame = ttk.Frame(add_frame)

        ttk.Label(self._key_frame, text=i18n.t("servers.key_file")).pack(side=tk.LEFT)
        self._srv_key_path_var = tk.StringVar()
        ttk.Entry(self._key_frame, textvariable=self._srv_key_path_var, width=25, state="readonly").pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(
            self._key_frame, text=i18n.t("servers.key_select"),
            style="Action.TButton", command=self._select_key_file
        ).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(self._key_frame, text=i18n.t("servers.key_passphrase")).pack(side=tk.LEFT)
        self._srv_key_pass_var = tk.StringVar()
        ttk.Entry(self._key_frame, textvariable=self._srv_key_pass_var, show="*", width=15).pack(side=tk.LEFT, padx=(4, 8))

        # Buttons row
        btn_row = ttk.Frame(add_frame)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        ttk.Button(
            btn_row, text=i18n.t("servers.btn_test"), style="Action.TButton",
            command=self._test_server
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            btn_row, text=i18n.t("servers.btn_add"), style="Action.TButton",
            command=self._add_server
        ).pack(side=tk.RIGHT)

        # Server list
        list_frame = ttk.LabelFrame(page, text=i18n.t("servers.saved"), padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "host", "port", "username", "auth")
        self._servers_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self._servers_tree.heading("name", text=i18n.t("servers.col_name"))
        self._servers_tree.heading("host", text=i18n.t("servers.col_host"))
        self._servers_tree.heading("port", text=i18n.t("servers.col_port"))
        self._servers_tree.heading("username", text=i18n.t("servers.col_username"))
        self._servers_tree.heading("auth", text=i18n.t("servers.col_auth"))
        self._servers_tree.column("name", width=120)
        self._servers_tree.column("host", width=180)
        self._servers_tree.column("port", width=60)
        self._servers_tree.column("username", width=100)
        self._servers_tree.column("auth", width=80)

        srv_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._servers_tree.yview)
        self._servers_tree.configure(yscrollcommand=srv_scrollbar.set)
        self._servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        srv_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(page)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self._btn_del_server = ttk.Button(
            btn_frame, text=i18n.t("servers.btn_delete"), style="Danger.TButton",
            command=self._delete_server, state=tk.DISABLED
        )
        self._btn_del_server.pack(side=tk.LEFT)

        self._servers_tree.bind("<<TreeviewSelect>>", self._on_server_select)

    def _on_auth_type_change(self, _event=None):
        auth = self._srv_auth_var.get()
        if auth == "key":
            self._pwd_frame.pack_forget()
            self._key_frame.pack(fill=tk.X, pady=2)
        else:
            self._key_frame.pack_forget()
            self._pwd_frame.pack(fill=tk.X, pady=2)

    def _select_key_file(self):
        ssh_dir = Path.home() / ".ssh"
        initial = ssh_dir if ssh_dir.exists() else Path.home()
        path = filedialog.askopenfilename(
            title=i18n.t("msg.select_key_file"),
            initialdir=str(initial),
        )
        if path:
            self._srv_key_path_var.set(path)

    # --- Data operations ---

    def _refresh_all(self):
        self._refresh_duration_combo()
        self._refresh_keys()
        self._refresh_servers()
        self._refresh_server_combo()

    def _refresh_duration_combo(self):
        durations = []
        for h in app_config.VALID_DURATIONS:
            label = i18n.t("keys.hour", h=h) if h == 1 else i18n.t("keys.hours", h=h)
            durations.append(label)
        self._key_duration_combo["values"] = durations
        if durations:
            self._key_duration_combo.current(0)

    def _refresh_keys(self):
        for item in self._keys_tree.get_children():
            self._keys_tree.delete(item)

        if not self._conn:
            return

        keys = database.list_keys(self._conn)
        for k in keys:
            remaining = key_manager.format_remaining_time(k["expires_at"], lang=i18n.get_lang())
            expired = key_manager.is_key_expired(k)
            status = i18n.t("keys.status_expired") if expired else i18n.t("keys.status_active")
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
            auth_label = i18n.t("servers.auth_key") if s.get("auth_type") == "key" else i18n.t("servers.auth_password")
            self._servers_tree.insert("", tk.END, iid=str(s["id"]), values=(
                s["name"], s["host"], s["port"], s["username"], auth_label
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

    def _get_server_auth(self, server: dict) -> dict:
        """Build SSH auth kwargs from server config."""
        if server.get("auth_type") == "key" and server.get("stored_key_path"):
            return {
                "key_path": server["stored_key_path"],
                "key_passphrase": self._srv_key_pass_var.get() or None,
            }
        return {
            "password": self._srv_pass_var.get() or self._key_password_var.get() or None,
        }

    # --- Key actions ---

    def _generate_key(self):
        server_id = self._get_selected_server_id()
        if server_id is None:
            messagebox.showwarning(i18n.t("dialog.warning"), i18n.t("msg.select_server"))
            return

        dur_str = self._key_duration_var.get()
        hours = int(dur_str.split()[0])
        label = self._key_label_var.get().strip()

        try:
            key = key_manager.generate_key(
                self._data_dir, self._conn, server_id, hours, label
            )
        except Exception as e:
            messagebox.showerror(i18n.t("dialog.error"), i18n.t("msg.key_gen_error", error=e))
            return

        # Deploy public key
        server = database.get_server(self._conn, server_id)
        if server:
            auth = self._get_server_auth(server)
            try:
                ssh_deploy.deploy_public_key(
                    host=server["host"],
                    username=server["username"],
                    port=server["port"],
                    public_key_path=key["public_key_path"],
                    **auth,
                )
                messagebox.showinfo(
                    i18n.t("dialog.success"),
                    i18n.t("msg.key_generated", host=server["host"])
                )
            except Exception as e:
                messagebox.showwarning(
                    i18n.t("dialog.warning"),
                    i18n.t("msg.key_gen_partial", error=e)
                )

        self._key_label_var.set("")
        self._refresh_keys()

    def _share_key(self):
        key = self._get_selected_key()
        if not key:
            return

        content = share.generate_claude_share(key)
        if clipboard.copy_to_clipboard(content):
            messagebox.showinfo(i18n.t("dialog.copied"), i18n.t("dialog.copied_msg"))
        else:
            win = tk.Toplevel(self)
            win.title(i18n.t("dialog.share_title"))
            win.geometry("600x400")
            text = tk.Text(win, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            text.insert("1.0", content)

    def _revoke_key(self):
        key = self._get_selected_key()
        if not key:
            return

        if not messagebox.askyesno(
            i18n.t("dialog.confirm_revoke_title"),
            i18n.t("dialog.confirm_revoke", name=key["key_name"], host=key["server_host"]),
        ):
            return

        server = database.get_server(self._conn, key["server_id"]) if self._conn else None

        def deploy_remove(**kwargs):
            auth = {}
            if server:
                auth = self._get_server_auth(server)
            return ssh_deploy.remove_public_key(
                host=key["server_host"],
                username=key["server_username"],
                port=22,
                public_key_path=key["public_key_path"],
                **auth,
            )

        ok, msg = key_manager.revoke_key(self._data_dir, self._conn, key["id"], deploy_remove)
        if ok:
            messagebox.showinfo(i18n.t("dialog.success"), msg)
        else:
            messagebox.showwarning(i18n.t("dialog.warning"), msg)
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
        auth_type = self._srv_auth_var.get()

        if not all([name, host, username]):
            messagebox.showwarning(i18n.t("dialog.warning"), i18n.t("msg.fields_required"))
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning(i18n.t("dialog.warning"), i18n.t("msg.invalid_port"))
            return

        # If key auth, copy key file to data dir
        stored_key_path = None
        if auth_type == "key":
            src_path = self._srv_key_path_var.get().strip()
            if not src_path:
                messagebox.showwarning(i18n.t("dialog.warning"), i18n.t("msg.fields_required"))
                return

            src = Path(src_path)
            if not src.exists():
                messagebox.showerror(i18n.t("dialog.error"), f"Key file not found: {src_path}")
                return

            # Copy key to data dir/keys/servers/
            srv_keys_dir = self._data_dir / "keys" / "servers"
            srv_keys_dir.mkdir(parents=True, exist_ok=True)
            dest_name = f"server_{uuid.uuid4().hex[:8]}_{src.name}"
            dest_path = srv_keys_dir / dest_name
            shutil.copy2(src, dest_path)

            # Set private permissions
            from ..permissions import set_private_file, set_private_dir
            set_private_dir(srv_keys_dir)
            set_private_file(dest_path)

            stored_key_path = str(dest_path)

        database.add_server(self._conn, name, host, port, username, auth_type, stored_key_path)
        messagebox.showinfo(i18n.t("dialog.success"), i18n.t("msg.server_added", name=name))

        self._srv_name_var.set("")
        self._srv_host_var.set("")
        self._srv_port_var.set("22")
        self._srv_user_var.set("")
        self._srv_pass_var.set("")
        self._srv_key_path_var.set("")
        self._srv_key_pass_var.set("")
        self._srv_auth_var.set("password")
        self._on_auth_type_change()

        self._refresh_servers()
        self._refresh_server_combo()

    def _delete_server(self):
        server = self._get_selected_server()
        if not server:
            return

        keys = database.list_keys(self._conn)
        active_keys = [k for k in keys if k["server_id"] == server["id"]]

        msg = i18n.t("dialog.confirm_delete", name=server["name"])
        if active_keys:
            msg += i18n.t("dialog.confirm_delete_keys", count=len(active_keys))

        if not messagebox.askyesno(i18n.t("dialog.confirm_delete_title"), msg):
            return

        for k in active_keys:
            key_manager.revoke_key(self._data_dir, self._conn, k["id"])

        # Remove stored key file
        if server.get("stored_key_path"):
            p = Path(server["stored_key_path"])
            if p.exists():
                p.unlink()

        database.delete_server(self._conn, server["id"])
        messagebox.showinfo(i18n.t("dialog.success"), i18n.t("msg.server_deleted", name=server["name"]))
        self._refresh_all()

    def _test_server(self):
        host = self._srv_host_var.get().strip()
        username = self._srv_user_var.get().strip()
        port_str = self._srv_port_var.get().strip()
        auth_type = self._srv_auth_var.get()

        if not all([host, username]):
            messagebox.showwarning(i18n.t("dialog.warning"), i18n.t("msg.fields_required"))
            return

        try:
            port = int(port_str)
        except ValueError:
            port = 22

        auth_kwargs = {}
        if auth_type == "key":
            key_src = self._srv_key_path_var.get().strip()
            if key_src:
                auth_kwargs["key_path"] = key_src
                auth_kwargs["key_passphrase"] = self._srv_key_pass_var.get() or None
        else:
            auth_kwargs["password"] = self._srv_pass_var.get() or None

        ok, msg = ssh_deploy.test_connection(host, username, port, **auth_kwargs)
        if ok:
            messagebox.showinfo(i18n.t("dialog.success"), i18n.t("msg.conn_ok"))
        else:
            messagebox.showerror(i18n.t("dialog.error"), i18n.t("msg.conn_fail", error=msg))

    def _on_server_select(self, _event):
        has_sel = bool(self._servers_tree.selection())
        self._btn_del_server.configure(state=tk.NORMAL if has_sel else tk.DISABLED)

    # --- Utility actions ---

    def _change_data_dir(self):
        path = filedialog.askdirectory(title=i18n.t("dialog.choose_data_dir"))
        if not path:
            return

        new_dir = Path(path) / "ssh-key-manager-data"
        if not messagebox.askyesno(
            i18n.t("dialog.confirm"),
            i18n.t("dialog.confirm_data_dir", path=new_dir)
        ):
            return

        app_config.set_data_dir_path(self._app_dir, new_dir)
        self.destroy()

    def _manual_cleanup(self):
        results = self._cleanup_expired()
        if results:
            messagebox.showinfo(i18n.t("dialog.info"), i18n.t("msg.cleanup_done", count=len(results)))
        else:
            messagebox.showinfo(i18n.t("dialog.info"), i18n.t("msg.no_expired"))
        self._refresh_keys()

    def _cleanup_expired(self) -> list[str]:
        if not self._conn:
            return []
        return key_manager.cleanup_expired_keys(self._data_dir, self._conn)

    def destroy(self):
        if self._conn:
            self._conn.close()
        super().destroy()
