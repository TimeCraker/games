# 2026-08-29 · Go 单测电池 Stage Spec — backend 从 0 到 1 建测试

> 执行者：Zcode（GLM-5.3-Flash）。本 spec 自包含，无需会话上下文。
> 复核：Claude（spec §4）→ 用户终审。
> 性质：**只加测试，不改业务代码**。

## §0 规则与护栏

- **为什么要做**：backend 现状 0 个 `_*_test.go`，CI（`.github/workflows/ci.yml`）只有 `go vet` + `go build`，连 `go test` 步骤都没有——`go test ./...` 基本跑不出东西。本站从 0 到 1 建单测电池。
- **铁律一（不改业务代码）**：只新增 `*_test.go`、CI 步骤、报告；业务 `.go` 文件 diff 必须为 0。测试过程中**发现疑似 bug → 记进报告，不修**（修不修由用户决定）。
- **铁律二（无设施跑绿）**：所有测试必须在**不起 MySQL / Redis / 不连网**的前提下 `go test ./...` 本地直接绿。依赖 DB/Redis/网络的包不硬上 mock 全家桶，跳过并列入报告清单。
- **铁律三（不放水）**：不许为变绿删断言、放宽断言、skip 正常用例。连续 2 轮同一红 → 停下报告。
- 依赖拉取若超时：`$env:GOPROXY="https://goproxy.cn"` 再试。
- 提交只 add 本站文件（backend/ 内的 _test.go、CI 文件、报告）；不 push，只本地 commit。

## §1 环境事实（已核实）

| 项 | 事实 |
|---|---|
| 仓库 | `C:\Users\TimeCraker\Desktop\my_workspace\games`（monorepo），工作树干净（7e2d389）；backend 在 `asternova/backend/` |
| 工具链 | go 1.25（go.mod），module `github.com/TimeCraker/game-backend-demo` |
| 依赖栈 | gin / gorilla-websocket / gorm+mysql / go-redis / jwt v5 / protobuf |
| 现有测试 | `_test.go` 0 个；`test/` 目录只有手动压测客户端 test_client.go（不是单测） |
| CI | 存在 ci.yml（位置 Stage 0 定位：games 根或 backend 下），现有 vet + build 两步 |
| 本地起停 | `scripts/local_up.ps1` 等（**本站不用**——测试不依赖起服务） |

## §2 契约

### 测试分层规则

| 层 | 处置 |
|---|---|
| 纯函数 / 校验 / 工具（无 DB/Redis/网络 import） | **必测**，表驱动风格 `t.Run` 子用例 |
| 依赖外部设施的服务层 | 跳过，报告列「需设施，未测」清单 |
| handler | 只测**入参校验与纯组装逻辑**（可无 gin engine 构造的部分）；起 HTTP server 的集成测试不做 |

### CI 追加

在跑 `go vet` 的那个 workflow 的对应 job 里，vet 之后加一步 `go test ./...`（与 vet 同一工作目录/同矩阵）。yaml 改完用 `yamllint` 或至少目测缩进核对，不破坏现有步骤。

### 报告

`asternova/backend/docs/2026-08-29-unit-tests-report.md`：包清单分类表（已测/需设施跳过）、测试数统计、疑似 bug 清单（只记不修）、复跑命令。

## §3 任务分 Stage

### Stage 0 · 盘点（先分类再动笔）

`go list ./...` 列全部包；逐包看 import：无 gorm/redis/mysql/网络 client 的纯逻辑包 → 「必测」清单；其余 → 「跳过」清单。同时定位 ci.yml 实际路径并通读。
完成标准：两份清单 + ci.yml 路径写进报告草稿；`go build ./...` 本地通过（确认工具链就绪）。

### Stage 1 · 逐包写测试

对「必测」清单逐包写 `_test.go`：表驱动、测**真行为**（输入→输出断言、边界值、错误路径），不测内部实现细节、不写同义反复断言（把实现抄一遍当期望值）。每完成 1-2 个包 commit 一次：
`test(backend): <包名> 单测 / unit tests for <pkg>`

### Stage 2 · 三级自验收（停下等确认）

- **L1**：`go vet ./...` + `go build ./...` + `go test ./...` 全 exit 0（**不启动任何设施**）。
- **L2**：`git diff --stat <起点>..HEAD` 确认业务 `.go` 文件改动为 0（只有 _test.go / ci.yml / 报告）；抽读自己写的 3 个测试确认断言的是外部可见行为。
- **L3**：报告成文（§2 报告节要求的四项）。停下等用户确认。

## §4 验收清单（Claude 复核用）

- [ ] `go test ./...` exit 0，且全程无 MySQL/Redis 进程依赖
- [ ] 业务代码 diff = 0；改动只见 _test.go / ci.yml / docs
- [ ] ci.yml 语法有效、test 步骤在 vet 后
- [ ] 抽读 3 个测试：断言真行为，非 mock 同义反复
- [ ] 疑似 bug 只记未修

## §5 参考

- monorepo 指引：`games/CLAUDE.md`、`games/asternova/backend/docs/roadmap.md`（Day 20「配置化」与测试无关，不在本站范围）
- Go 表驱动测试惯例：标准库 testing，`t.Run` + `t.Errorf`
