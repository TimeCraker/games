# 2026-08-29 · Go 单测电池验收报告

> 对应 Stage Spec：[2026-08-29-unit-tests-spec.md](./2026-08-29-unit-tests-spec.md)
> 执行：Zcode（GLM-5.3-Flash）· 起点 commit `94e9368` · 全程未启动 MySQL/Redis/任何网络服务
> 铁律遵守情况：业务 `.go` 改动 **0**；全部测试无设施跑绿；未删/未放宽任何断言。

## 一、包清单分类

| 包 | 处置 | 说明 |
|---|---|---|
| `services/battle` | ✅ 已测（3 文件） | 向量数学、玩家状态机、战斗仲裁——纯内存逻辑，本站核心 |
| `services/match` | ✅ 已测 | 匹配队列防抖/移除/1s Tick 发车 |
| `services/auth/utils` | ✅ 已测（jwt 部分） | JWT 签发/解析/篡改拒绝；`email.go`（SMTP 发信）属网络路径未测 |
| `services/auth/middleware` | ✅ 已测 | `CreateTestContext` 验证 401/格式校验/放行 + userID 注入 |
| `services/auth/handlers/account` | ✅ 已测（校验层） | 纯函数（`randomHex`/`randomGuestIdentity`/`isValidPassword`）+ handler 入参校验分支（均位于触达 DB/Redis 之前） |
| `services/gateway/handlers` | ✅ 已测（校验层） | `HandleWS` token/roomId 校验分支 + Hub 房间守卫（`RoomHasUser`/`JoinRoom`/`LeaveRoom` 边界）；WS 升级与读写循环未测 |
| `services/auth/models` | ✅ 已测（轻量） | 下行 JSON 字段契约（前端依赖 `user_id`/`x/y/z`/`created_at` 等 key） |
| `services/proto` | ✅ 已测（轻量） | `GameMessage` Marshal/Unmarshal 往返一致性 + 非法字节拒绝 |
| `.`（main） | ⏭️ 跳过 | 服务入口装配，无独立纯函数 |
| `services/auth/db` | ⏭️ 需设施，未测 | MySQL/Redis 直连（惰性初始化，import 不拨号） |
| `services/auth/handlers/send_email` | ⏭️ 需设施，未测 | Redis 限流 + SMTP 发信，无纯函数 |
| `test` | ⏭️ 跳过 | 手动压测客户端（main 包），非单测对象 |

## 二、测试数统计

- **测试文件**：10 个（见文末清单）
- **顶层测试函数**：59 个；**含 `t.Run` 子用例共 223 例**，`--- FAIL` = 0
- **L1 三级验证**：`go vet ./...` exit 0 · `go build ./...` exit 0 · `go test ./...` 全 ok（无任何外部设施）
- **L2 diff 验证**：`git diff --stat 94e9368..HEAD` = 10 × `_test.go` + 1 × `ci.yml`，全部为新增行，业务 `.go` diff = 0

### 测试断言的都是外部可见行为（抽读 3 例）

1. `battle/room_test.go → TestRunCombatArbiterOneSidedHit`：只构造双方位置/状态输入，断言仲裁器输出（受害者 HP-30 且进硬直、攻击方不掉血），不复刻内部距离公式。
2. `auth/utils/jwt_test.go → TestParseTokenRejectsWrongSecret`：用另一密钥签发伪造 token，断言被拒绝——验证的是安全契约而非签名实现。
3. `auth/middleware/middleware_test.go`：表驱动断言 HTTP 状态码（401/200）、`c.IsAborted()`、`c.Get("userID")` 注入值——全部为请求方可观测结果。

## 三、疑似问题清单（只记不修，修否由用户决定）

| # | 位置 | 问题 | 等级 |
|---|---|---|---|
| 1 | `services/auth/utils/email.go:15` | **SMTP 授权码硬编码入库**（`SenderSecret = "wrwynnhosmzxeaja"`）。任何有仓库读权限者可冒用发件箱；建议迁移环境变量并立即吊销该授权码 | 高（安全） |
| 2 | `services/auth/utils/jwt.go:9` | **JWT 密钥硬编码** `"your-secret-key"`（注释自陈应改环境变量）。持源码者可伪造任意用户 token | 高（安全） |
| 3 | `services/auth/models/user.go:8` | `Password` 字段无 `json:"-"` 标签，`json.Marshal(User)` 会泄漏密码哈希；当前 handler 均手拼 `gin.H` 未触发，属契约层隐患 | 中（安全） |
| 4 | `services/gateway/handlers/websocket.go:28` | WebSocket `Upgrader.CheckOrigin` 恒 `true`，存在跨站 WebSocket 劫持（CSWSH）风险 | 中（安全） |
| 5 | `services/auth/handlers/account/reset_password.go:53` | 密码校验用 `TrimSpace` 后的值，bcrypt 存储原始值：`" abc123 "` 可通过校验却按含空格存储，登录需精确复现空格，行为不一致 | 低 |
| 6 | `services/match/matcher.go:69` | `Matcher.Start` 的 ticker 无 `Stop`、goroutine 无退出机制，匹配引擎无法优雅关停（常驻进程影响小） | 低 |
| 7 | `services/auth/handlers/send_email/email.go:51` | `rand.Seed` 自 Go 1.20 起已废弃（工具链 1.25/1.26），可删 | 低 |

## 四、复跑命令

```powershell
cd asternova/backend
go vet ./...      # exit 0
go build ./...    # exit 0
go test ./...     # 全 ok，无需 MySQL/Redis/网络
```

## 五、改动文件清单

```
asternova/backend/.github/workflows/ci.yml                              (+3,  vet 后加 go test 步骤)
asternova/backend/services/battle/math_test.go                          (新增)
asternova/backend/services/battle/player_state_test.go                  (新增)
asternova/backend/services/battle/room_test.go                          (新增)
asternova/backend/services/match/matcher_test.go                        (新增)
asternova/backend/services/proto/game_test.go                           (新增)
asternova/backend/services/auth/utils/jwt_test.go                       (新增)
asternova/backend/services/auth/middleware/middleware_test.go           (新增)
asternova/backend/services/auth/handlers/account/account_test.go        (新增)
asternova/backend/services/gateway/handlers/handlers_test.go            (新增)
asternova/backend/services/auth/models/models_test.go                   (新增)
```

本地 commit 5 个（未 push）：
```
1a24a38 ci(backend): 在 vet 后追加 go test 步骤 / add go test step after vet
923b976 test(backend): account/gateway/models 包单测（校验分支、Hub 守卫、JSON 契约）
0c222f6 test(backend): auth utils 与 middleware 单测（JWT 往返与鉴权中间件）
09d9237 test(backend): match/proto 包单测（匹配队列与协议往返）
120eced test(backend): battle 包单测（向量数学/状态机/战斗仲裁）
```

## 六、Spec §4 验收清单自评

- [x] `go test ./...` exit 0，全程无 MySQL/Redis 进程依赖
- [x] 业务代码 diff = 0；改动只见 _test.go / ci.yml / docs（本报告）
- [x] ci.yml 语法有效（PyYAML 实测通过）、test 步骤在 vet 后
- [x] 抽读 3 个测试：断言真行为，非 mock 同义反复（见 §二）
- [x] 疑似 bug 只记未修（§三 7 条，未动任何业务代码）
