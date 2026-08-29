# 2026-08-29 · 安全 env 化修复 Stage Spec — JWT/SMTP 密钥出库 + WS Origin 白名单

> 执行者：Zcode（GLM-5.3-Flash）。本 spec 自包含，无需会话上下文。
> 复核：Claude（spec §4）→ 用户终审。
> 性质：安全修复。**三个修复点之外的业务代码 diff 必须为 0。**

## §0 规则与护栏

- **为什么要做**：本仓库 PUBLIC，三处已核实的问题：
  1. `services/auth/utils/jwt.go:9` 密钥硬编码 `"your-secret-key"`——持源码者可伪造任意用户 token；
  2. `services/auth/utils/email.go:15` SMTP 授权码明文（已迁入 env，代码里必须清掉）；
  3. `services/gateway/handlers/websocket.go:28` `CheckOrigin` 恒 `true`——任意网站可借玩家浏览器身份建 WS 连接。
- **env 值永不进 git**：密钥值已由指挥官写入服务器 `~/game-backend-demo/.env` 与本地 `asternova/backend/.env`（`games/.gitignore` 已含 `.env`）。本站只写代码 + `.env.example`（占位值），任何真实密值出现在提交里 = FAIL。
- 只动四个目标文件 + 新增 `.env.example` + 报告；不部署（指挥官负责）；不清 git 历史（用户拍板）；连续 2 红停。
- 依赖拉取超时：`$env:GOPROXY="https://goproxy.cn"`。

## §1 环境事实（已核实）

| 项 | 事实 |
|---|---|
| 仓库 | `C:\Users\TimeCraker\Desktop\my_workspace\games`（PUBLIC），backend 在 `asternova/backend/`，go 1.25 |
| 服务器 env 机制 | systemd unit `asternova-server.service` 已有 `EnvironmentFile=-/home/ubuntu/game-backend-demo/.env`、WorkingDirectory 同目录——**服务端 env 装载已就绪，本站零服务器操作** |
| 三键（两端 .env 已就位） | `JWT_SECRET`（随机 hex）/ `SMTP_SECRET`（原授权码值）/ `WS_ORIGIN_ALLOWLIST`（`https://game.asterforge.top,http://localhost:3001,http://127.0.0.1:3001`） |
| 测试现状 | 10 个 `_test.go` 全绿（含 `services/auth/utils/jwt_test.go`，现直接用包级 `jwtSecret`） |
| 允许新增依赖 | 仅 `github.com/joho/godotenv`（本地开发从 `.env` 读环境变量的惯例做法；服务器走 systemd，不依赖它） |

## §2 契约

### 1 · JWT（jwt.go）

- 删包级 `var jwtSecret = []byte("your-secret-key")`，改为调用点取值：

```go
func jwtSecretKey() []byte {
    s := os.Getenv("JWT_SECRET")
    if len(s) < 16 {
        log.Fatal("JWT_SECRET not set or shorter than 16 chars (see .env.example)")
    }
    return []byte(s)
}
```

- **为什么不用 `init()` 读一次**：包 init 在测试设 env 之前跑，会把全部测试炸掉。调用点读取 + `log.Fatal` 兜底（缺密钥 = 起不来，fail loud）。
- `GenerateToken` / `ParseToken` 等所有原引用点改走 `jwtSecretKey()`。
- 测试改造：`jwt_test.go` 加 `TestMain` 里 `os.Setenv("JWT_SECRET", "unit-test-secret-0123456789abcdef")`；保留全部既有断言，另加一条「伪造签名 token 被拒绝」。

### 2 · SMTP（email.go）

- 删 `SenderSecret` 常量；发送处 `os.Getenv("SMTP_SECRET")`；空值 → 返回明确 error（`SMTP_SECRET not set`），**不 log.Fatal**（邮件非关键路径，缺配置不该打死整个服务）。
- `SMTPPort` / `SenderEmail` 非密钥，保持常量不动。
- 测试：新增空值错误路径用例（不实际发信、不碰网络）。

### 3 · WebSocket Origin（websocket.go）

- `CheckOrigin` 改白名单判定：

```go
func originAllowed(origin string) bool {
    // localhost/127.0.0.1 任意端口放行（本地开发）
    if strings.HasPrefix(origin, "http://localhost:") || strings.HasPrefix(origin, "http://127.0.0.1:") {
        return true
    }
    list := os.Getenv("WS_ORIGIN_ALLOWLIST")
    if list == "" {
        list = "https://game.asterforge.top" // 缺省只认线上域
    }
    for _, o := range strings.Split(list, ",") {
        if strings.TrimSpace(o) == origin {
            return true
        }
    }
    return false
}
```

- 测试：表驱动（`t.Run`）覆盖——线上域放行 / `https://evil.example` 拒绝 / `http://localhost:3001` 放行 / env 缺省回落线上域。用 `t.Setenv`。

### 4 · .env.example（进 git，占位值）

```
JWT_SECRET=<random hex >= 32 chars>
SMTP_SECRET=<SMTP auth code>
WS_ORIGIN_ALLOWLIST=https://game.asterforge.top,http://localhost:3001,http://127.0.0.1:3001
```

### 5 · godotenv 接线

`go get github.com/joho/godotenv`；main 包（`main.go`）init 或 main 首行 `_ = godotenv.Load()`（文件缺失静默跳过）。仅此一处。

## §3 任务分 Stage

- **Stage 0**：通读三文件 + `main.go`，列 secret 引用点清单（`jwtSecret` / `SenderSecret` 的全部使用处）进报告草稿。
- **Stage 1**：JWT env 化 + godotenv + jwt_test 改造 → `go test ./...` 全绿。commit：`fix(auth): JWT 密钥出库改环境变量 / move JWT secret to env`
- **Stage 2**：SMTP env 化 + 空值错误路径测试 → 全绿。commit：`fix(auth): SMTP 授权码出库改环境变量 / move SMTP secret to env`
- **Stage 3**：CheckOrigin 白名单 + 表驱动测试 + `.env.example` → 全绿。commit：`fix(gateway): WebSocket Origin 白名单校验 / whitelist WebSocket origins`
- **Stage 4 三级自验收（停下等确认）**：
  - L1：`go vet ./...` + `go build ./...` + `go test ./...` 全 exit 0。
  - L2：`git diff --stat <起点>..HEAD` 只含三个目标文件 + `.env.example` + 报告 + `go.mod`/`go.sum`（godotenv）；`grep -rn "your-secret-key" services/` 0 命中；`git status` 无 `.env` 出现在未跟踪列表（被 ignore）。
  - L3：报告 `docs/2026-08-29-security-env-report.md`（引用点清单、改动摘要、测试数、遗留）。停下。

## §4 验收清单（Claude 复核用）

- [ ] 三文件 grep 明文密钥 0 命中；`.env` 被 gitignore
- [ ] go 全家桶 exit 0；业务其他代码 diff = 0
- [ ] 测试断言真行为：伪造 token 拒绝、异域 Origin 拒绝、缺 SMTP_SECRET 报错
- [ ] `.env.example` 占位值，无真实密值

## §5 部署注记（指挥官线，不在本站范围）

三键已存两端（服务器 `~/game-backend-demo/.env` / 本地 `backend/.env`），deploy 仓 `backup-from-servers.ps1` 巡检时会把服务器 env 备份进私有仓形成第三份。代码合入后由指挥官 push + 服务器 `git pull && go build && systemctl restart asternova-server`；**重启后全部现有登录态失效（换密钥的一次性代价），属预期**。
