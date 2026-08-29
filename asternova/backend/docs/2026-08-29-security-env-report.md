# 2026-08-29 · 安全 env 化修复验收报告

> 对应 Stage Spec：[2026-08-29-security-env-spec.md](./2026-08-29-security-env-spec.md)
> 执行：Zcode（GLM-5.3-Flash）· 起点 commit `2f07d5d` · 全程未启动 MySQL/Redis/任何网络服务
> 性质：安全修复（JWT / SMTP 密钥出库 + WS Origin 白名单），三修复点之外业务代码 diff = 0

## 一、Stage 0 · secret 引用点清单（盘点结论）

| 密钥 | 引用点（修复前） | 处置 |
|---|---|---|
| JWT `jwtSecret` | `services/auth/utils/jwt.go:9`（定义，硬编码）、`:29`（GenerateToken）、`:35`（ParseToken keyFunc）、`jwt_test.go:98`（测试签过期 token） | 全部改走 `jwtSecretKey()` |
| SMTP `SenderSecret` | `services/auth/utils/email.go:15`（定义，明文授权码）、`:20`（smtp.PlainAuth） | 常量删除，改 `os.Getenv("SMTP_SECRET")` |
| WS `CheckOrigin` | `services/gateway/handlers/websocket.go:28`（恒 true）、`:65`（Upgrade 调用点，不改） | 改 `originAllowed()` 白名单 |
| `SenderEmail` / `SMTPHost` / `SMTPPort` | email.go 三处使用 | 非密钥，保持常量不动 |

环境核实：`asternova/backend/.env` 存在且被 `backend/.gitignore:16`（`.env`）忽略；godotenv 原不在 go.mod；服务器 systemd `EnvironmentFile` 已就绪，本站零服务器操作。

## 二、改动摘要（12 文件，+137/−12）

| 文件 | 改动 |
|---|---|
| `services/auth/utils/jwt.go` | 删包级 `jwtSecret`，新增 `jwtSecretKey()`：调用点读 `JWT_SECRET`，缺失或 <16 字符 `log.Fatal`（fail loud）。**不用 init() 读一次**：包 init 先于测试的 `os.Setenv` 执行会炸掉全部测试。`GenerateToken`/`ParseToken` 改走它 |
| `main.go` | `_ = godotenv.Load()` 于 `main()` 首行（文件缺失静默跳过；服务器走 systemd 不依赖它） |
| `services/auth/utils/email.go` | 删 `SenderSecret` 常量；`SendVerificationEmail` 开头读 `SMTP_SECRET`，空值返回 `errors.New("SMTP_SECRET not set")`（邮件非关键路径，不 log.Fatal），在触达网络前短路 |
| `services/gateway/handlers/websocket.go` | `CheckOrigin` 恒 true → `originAllowed()`：localhost/127.0.0.1 任意端口放行 + `WS_ORIGIN_ALLOWLIST` 逐项匹配（TrimSpace），env 缺省回落只认线上域 |
| `.env.example`（新增） | 三键占位值，无真实密值 |
| `go.mod` / `go.sum` | 新增 `github.com/joho/godotenv v1.5.1`（direct） |
| `jwt_test.go` | 新增 `TestMain` 注入测试密钥；expired 用例改用 `jwtSecretKey()`；既有断言全保留（含伪造签名拒绝 `TestParseTokenRejectsWrongSecret`） |
| `email_test.go`（新增） | `SMTP_SECRET` 空值错误路径（`t.Setenv`，不实际发信、不碰网络） |
| `websocket_test.go`（新增） | `originAllowed` 表驱动 10 子用例（`t.Setenv`）：线上域放行 / 异域拒绝 / localhost 任意端口 / 清单外子域拒绝 / 空白裁剪匹配 / env 缺省回落 / 空 Origin |
| `middleware_test.go`、gateway `handlers_test.go` | 各加 `TestMain` 设 `JWT_SECRET`（**必要连带**：两包测试调 `utils.GenerateToken`，密钥 env 化后不设即 fail loud） |

## 三、测试与验证

- **测试数**：63 个顶层测试函数 / 176 个 RUN 用例（含子测试），`--- FAIL` = 0；本轮净增 2 个测试函数 + 10 个 Origin 子用例 + 1 个 SMTP 错误路径用例
- **L1**：`go vet ./...` exit 0 · `go build ./...` exit 0 · `go test ./...` **真实 exit 0**（重定向后单独取 `$?`，无管道掩码），0 行 FAIL
- **L2**：
  - `git diff --stat 2f07d5d..HEAD` 仅含三个目标文件 + main.go + go.mod/go.sum + 5 个测试文件 + `.env.example`，其余业务代码 diff = 0
  - `grep -rn "your-secret-key" services/ main.go` → **0 命中**；SMTP 授权码原值全仓 grep → **0 命中**
  - `git check-ignore asternova/backend/.env` 命中（被 `backend/.gitignore:16` 忽略）；`git status` clean，`.env` 未出现在未跟踪列表
  - `.env.example` 未被 ignore 规则匹配，仅占位值进 git
- **断言真行为自检**：伪造密钥签发的 token 被拒绝、异域 Origin（含伪装子域）被拒绝、缺 `SMTP_SECRET` 报明确错误——均为请求方/攻击方可观测行为，非实现复刻

## 四、提交清单（本地 3 个 commit，未 push）

```
6c2ca90 fix(gateway): WebSocket Origin 白名单校验 / whitelist WebSocket origins
2de4288 fix(auth): SMTP 授权码出库改环境变量 / move SMTP secret to env
7b879ca fix(auth): JWT 密钥出库改环境变量 / move JWT secret to env
```

## 五、遗留（不在本站范围）

1. **git 历史仍含明文密钥**：`jwt.go`/`email.go` 的历史提交可追溯出旧密值。spec 明示本站不清历史（用户拍板）；由于换钥已属部署注记内动作，旧 JWT 密钥轮换后历史泄露的 `"your-secret-key"` 不再有效；**SMTP 授权码历史泄露仍在有效期，建议在服务端 .env 落地新授权码后于 QQ 邮箱后台吊销旧值**。
2. **重启代价**：换 `JWT_SECRET` 后全部现有登录态失效（spec §5 已预期）。
3. `main.go` 全局 CORS 仍为 `Access-Control-Allow-Origin: *`（非本站三修复点，仅记录）。
4. 服务器 `.env` 三键由指挥官核对（本站未读未传任何真实密值）。

## 六、Spec §4 验收清单自评

- [x] 三文件 grep 明文密钥 0 命中；`.env` 被 gitignore
- [x] go 全家桶（vet/build/test）exit 0；业务其他代码 diff = 0
- [x] 测试断言真行为：伪造 token 拒绝、异域 Origin 拒绝、缺 SMTP_SECRET 报错
- [x] `.env.example` 占位值，无真实密值
