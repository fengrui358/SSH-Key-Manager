# SSH Key Manager

跨平台便携式 SSH 临时密钥管理工具，专为安全地给 Claude Code 等 AI 助手授权服务器访问设计。

## 功能特性

- **临时密钥生成** — 生成带有效期的 ed25519 密钥（1/2/4/8/24/72 小时）
- **一键部署** — 自动将公钥部署到远程服务器的 `authorized_keys`
- **服务器管理** — 添加、删除、测试常用服务器连接
- **Claude Code 分享** — 一键生成格式化的密钥信息并复制到剪贴板
- **密钥撤销** — 同时从服务器和本地删除密钥
- **自动清理** — 启动时自动清理过期密钥，也支持手动触发
- **数据目录分离** — 数据目录可放在 OneDrive/坚果云/U 盘中跨设备同步

## 下载安装

从 [GitHub Releases](https://github.com/fengrui358/SSH-Key-Manager/releases) 下载对应平台版本：

| 平台 | 文件 | 要求 |
|------|------|------|
| macOS | `ssh-key-manager` | macOS 12+ |
| Windows | `ssh-key-manager.exe` | Windows 10+ |

无需安装任何依赖，下载后直接运行。

### macOS 首次运行

```bash
chmod +x ssh-key-manager
./ssh-key-manager
```

如果 macOS 阻止运行，前往 **系统设置 → 隐私与安全性** 点击「仍要打开」。

### Windows 运行

双击 `ssh-key-manager.exe`，如果 SmartScreen 弹窗，点击「更多信息」→「仍要运行」。

## 使用说明

### 1. 首次启动 — 选择数据目录

首次运行会弹出对话框让你选择数据目录。所有密钥文件、数据库和配置都保存在这个目录中。

建议将数据目录放在同步工具的目录下（如 OneDrive、iCloud、坚果云），这样可以在不同电脑之间无缝同步。

数据目录结构：

```
ssh-key-manager-data/
├── config.json       # 应用配置
├── data.db           # SQLite 数据库
└── keys/             # SSH 密钥文件
    ├── id_ed25519_xxx
    └── id_ed25519_xxx.pub
```

### 2. 添加服务器

1. 点击左侧 **Server Management**
2. 填写服务器信息：
   - **Name** — 显示名称（如 `prod-server`）
   - **Host** — 服务器地址（IP 或域名）
   - **Port** — SSH 端口（默认 22）
   - **Username** — 登录用户名
   - **Password** — 登录密码（用于部署公钥，不会保存）
3. 点击 **Test Connection** 验证连接
4. 点击 **Add Server** 保存

### 3. 生成密钥并部署

1. 点击左侧 **Key Management**
2. 在生成区域选择：
   - **Server** — 目标服务器
   - **Duration** — 密钥有效期
   - **Label** — 密钥标签（可选）
   - **Server Password** — 用于部署公钥的服务器密码
3. 点击 **Generate & Deploy**
4. 程序会自动生成密钥对并将公钥部署到服务器

### 4. 分享给 Claude Code

1. 在密钥列表中选中一个密钥
2. 点击 **Share for Claude**
3. 格式化的密钥信息会自动复制到剪贴板，内容包括：
   - 服务器连接信息
   - 私钥内容
   - 快速连接命令
4. 将内容粘贴给 Claude Code 即可使用

### 5. 撤销密钥

1. 在密钥列表中选中要撤销的密钥
2. 点击 **Revoke Key**
3. 确认操作后，程序会：
   - 从服务器移除公钥
   - 删除本地密钥文件
   - 从数据库移除记录

### 6. 切换数据目录

点击左侧 **Data Directory** 按钮可以随时切换数据目录位置。切换后程序会重启。

### 7. 清理过期密钥

程序启动时会自动清理所有过期密钥。也可以点击左侧 **Cleanup Expired** 手动触发。

## 安全说明

- 私钥文件权限设为 `0o600`（仅 owner 可读写），密钥目录权限设为 `0o700`
- 程序启动时自动检查并修复权限（仅 macOS/Linux）
- 私钥仅在「分享给 Claude」时才会被读取，不会在界面上明文显示
- 所有数据完全本地存储，不向任何第三方发送数据
- 密钥到期后自动清理，避免长期暴露

## 从源码运行

需要 [uv](https://docs.astral.sh/uv/) 包管理器：

```bash
git clone https://github.com/fengrui358/SSH-Key-Manager.git
cd SSH-Key-Manager
uv sync
uv run python -m src.ssh_key_manager
```

## 发布新版本

1. 修改 `src/ssh_key_manager/__init__.py` 中的 `__version__`
2. 提交并打 tag：

```bash
git add -A && git commit -m "release: v0.2.0"
git tag v0.2.0
git push origin main --tags
```

3. GitHub Actions 会自动构建 macOS + Windows 并创建 Release

## 技术栈

| 组件 | 选择 |
|------|------|
| 语言 | Python 3.10+ |
| GUI | tkinter + ttk |
| SSH | paramiko |
| 密钥生成 | cryptography + PyNaCl |
| 存储 | SQLite |
| 打包 | PyInstaller |
| 包管理 | uv |

## License

MIT
