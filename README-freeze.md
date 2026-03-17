# 🎮 FreezeHost 自动续期

使用 GitHub Actions 自动续期 FreezeHost 免费服务器。

## 📋 项目结构

```
auto_scripts/                      # 公开仓库
├── .github/workflows/
│   └── freeze-AutoRenew.yml      # GitHub Actions 工作流
├── README.md                      # 项目说明
└── ...其他文件
```

## ⚙️ 配置步骤

### 1️⃣ 创建仓库
  
- **公开仓库**：
  - 包含 `.github/workflows/freeze-AutoRenew.yml`、`README.md`

### 2️⃣ 添加 GitHub Secrets

进入公开仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| 🔑 Secret 名称 | 📝 说明 | ✅ 必填 |
|---|---|---|
| `FREEZE_DISCORD_ACCOUNT` | Discord 账号配置 | ✅ |
| `PRIVATE_REPO_TOKEN` | 私有仓库访问令牌 | ✅ |
| `HY2_PROXY_URL` | Hysteria2 代理 URL | 可选 |
| `SOCKS_PORT` | SOCKS5 端口（默认 51080） | 可选 |

### 3️⃣ 配置 FREEZE_DISCORD_ACCOUNT

**格式**：每行一个账号，用逗号分隔字段

```
email1@example.com,password1,tg_token1,tg_id1
email2@example.com,password2,tg_token2,tg_id2
email3@example.com,password3
```

**字段说明**：
- `email` - Discord 邮箱（必填）
- `password` - Discord 密码（必填）
- `tg_token` - Telegram Bot Token（可选）
- `tg_id` - Telegram 用户 ID（可选）

**支持的格式**：
- 2 字段：`email,password`（无 TG 通知）
- 4 字段：`email,password,tg_token,tg_id`（完整配置）
- 混合：可同时使用 2 字段和 4 字段账号

### 4️⃣ 配置 HY2_PROXY_URL（可选）

如需使用 Hysteria2 代理，格式为：
```
hysteria2://auth_string@host:port?sni=domain&insecure=0&alpn=h3
```

示例：
```
hysteria2://mypassword@proxy.example.com:443?sni=proxy.example.com&insecure=0&alpn=h3
```

### 5️⃣ 配置 Actions 权限

进入公开仓库 → **Settings** → **Actions** → **General** → **Workflow permissions**：

选择 **Read and write permissions**（读写权限），这样工作流才能：
- 提交执行时间到仓库
- 上传失败截图作为工件

或者在 `.github/workflows/freeze-AutoRenew.yml` 中已配置：
```yaml
permissions:
  contents: write
```

### 6️⃣ 启用 Actions

进入公开仓库 **Actions** 标签页，点击 **Enable GitHub Actions**。

### 7️⃣ 手动触发测试

**Actions** → **🔄 FreezeHost 自动续期** → **Run workflow**

## 🔐 权限配置

GitHub Actions 工作流需要以下权限：

| 权限 | 说明 | 用途 |
|---|---|---|
| `contents: write` | 读写仓库内容 | 提交执行时间到仓库、上传工件 |

**配置方式**：
1. 在 `.github/workflows/freeze-AutoRenew.yml` 中已配置（推荐）
2. 或在仓库 Settings → Actions → General → Workflow permissions 中选择 **Read and write permissions**

## 🕐 运行时间

- **定时运行**：每 2 天早上 9 点 23 分（北京时间）
- **手动触发**：可随时在 Actions 页面手动运行
- **修改时间**：编辑 `.github/workflows/freeze-AutoRenew.yml` 中的 `cron` 表达式

## 📊 续期结果说明

| 状态 | 说明 |
|---|---|
| ✅ 续期成功 | 服务器续期成功，TG 已推送通知 |
| ⏰ 尚未到续期时间 | 今日已续期或暂不需要续期 |
| ⚠️ 余额不足 | 金币不足，请前往挂机页面赚取金币 |
| ❌ Discord 登录失败 | 账号密码错误或触发了 2FA/验证码 |
| ❌ 脚本异常 | 其他异常，查看 failure-screenshots |

## 📨 Telegram 通知

### 单账号通知
每个账号处理完成后，如配置了 TG，会收到单独的通知消息。

### 批量统计通知
当处理 2 个或以上账号时，会向**第一个账号**的 TG 发送统计信息：
- 总账户数
- 登录成功/失败数
- 续期成功/失败/跳过数
- 运行时间和 IP 信息

## 🌐 代理支持

### 无代理模式
直接连接，不需要配置 `HY2_PROXY_URL`。

### Hysteria2 代理模式
1. 配置 `HY2_PROXY_URL` Secret
2. 工作流会自动安装 Hysteria2
3. 自动建立 SOCKS5 代理连接
4. 所有请求通过代理转发

## 🔧 故障排查

### 登录失败
- 检查 Discord 账号密码是否正确
- 检查是否启用了 2FA（目前不支持）
- 查看 failure-screenshots 中的截图

### 续期失败
- 检查金币余额是否充足
- 查看错误日志中的具体原因
- 检查网络连接和代理配置

### TG 通知未收到
- 检查 `tg_token` 和 `tg_id` 是否正确
- 确保 Telegram Bot 已启用
- 查看工作流日志中的 TG 推送错误信息

## 📝 日志查看

在 GitHub Actions 中查看详细日志：
1. 进入仓库 **Actions** 标签页
2. 选择最近的工作流运行
3. 点击 **🔄 执行续期** 查看详细日志
4. 失败时可下载 **failure-screenshots** 工件

## ⚠️ 注意事项

- 不支持 Discord 2FA（双因素认证）
- 不支持 Discord 邮箱验证
- 代理配置仅支持 Hysteria2 协议
- 建议每个账号配置不同的 TG 通知，便于区分
- 不要在公开仓库中暴露 Discord 账号密码，使用 GitHub Secrets 管理

## 📄 许可证

MIT License

## 🙏 致谢

感谢 [losy-mify/Freeze-Renew](https://github.com/losy-mify/Freeze-Renew/) 项目的启发和参考。
