# UI 细节打磨 · AUDIT

> 目标：前端 UI 细节打磨（零人类参与 · 永续循环版）
> 仓库：当前目录（AsterNova Game Matrix monorepo）｜ 前端：`asternova/web-client`（Next.js 16.3.0 + React 19 + Tailwind v4 + framer-motion + zustand）
> **站点端口：http://127.0.0.1:4105**（本任务自建服务器；3000/3100 被宿主机上他人遗留进程占用，详情见下）
> 审查浏览器：Chrome 153 headless，CDP 端口 9333
> 临时目录（不进仓库/不提交）：`.ui-polish/artifacts/`（截图 + 扫描 JSON）、`.ui-polish/chrome-profile/`、`.ui-polish/tools/audit.mjs`（零依赖审计脚本）
> 主题：站点为深空黑单主题（ThemeProvider forcedTheme="dark"）→ 按 Goal 只扫深色主题，不新增浅色主题

## 覆盖矩阵

| 路由 | 桌面 1440×900 | 移动 375×812 | 备注 |
| --- | --- | --- | --- |
| / | ✅ R1 | ✅ R1 | 首页黑洞观象台 |
| /login | ✅ R1 | ✅ R1 | 登录（含忘记密码弹层） |
| /lobby | ✅ R1（种子登录态渲染） | ✅ R1 | 大厅（需登录，审计用 localStorage 种子） |
| /arena | ⚠️ R1（守卫态） | ⚠️ R1 | 无真实对战会话时守卫渲染「战斗舱未解锁」并 4s 内跳 /login；深层战场 HUD 待后端起后再审计 |
| /shoot-them-all | ✅ R1 | ✅ R1 | Pixi 弹射 |
| /lets-running | ✅ R1 | ✅ R1 | 跑酷 |
| /merge | ✅ R1 | ✅ R1 | 合成 |
| /nebula-survivor | ✅ R1 | ✅ R1 | 肉鸽生存 |
| /xiaoxiaole | ✅ R1 | ✅ R1 | 三消 iframe |
| /this-route-does-not-exist | ✅ R1 | ✅ R1 | 404 品牌页验证 |

## 环境与踩坑（建立于 R1）

1. **沙箱禁 pipe stdio → `next dev`（fork 渲染进程）与 `next build`（page-data fork 11 workers）均 EPERM**。修法：`next.config.ts` 增加 `experimental.workerThreads: true`（Next 16 支持，build/index.js 据此走 jest-worker 线程模式），build 全绿。`next dev` 依旧不可用（其 fork 无条件），**本任务一律用 `npm run build && npm run start -- -p 4105`** 提供站点，验证脚本以重建后复验为准。
2. **端口占用**：宿主机 3000（旧版 Asternova 构建，与本仓库当前 HEAD 不符）与 3100（无关项目）已有进程监听；沙箱内 Get-NetTCPConnection 看不到他人进程。故站点定在 **4105**，重试不撞口。
3. **HMR 不可用**：每次修复后需重新 `npm run build` 并重启 `next start` 才能复验（本任务环境约束，非代码问题）。
4. 幂等性：每轮重读本文件「剩余队列」查重，防止重复修。

<!-- 每轮结果由执行循环追加在下方 -->

---

## R1 · 执行记录（环境建立 + 首轮审计）
（待审计完成后填写）

