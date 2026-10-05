# Stage Spec：web-client 性能二期 + 官网内容化（Perf 55+ → 70+ · 从「壳」到玩家回访地）

> **status: DRAFT（待所有者评审，非实施指令）**。本文为草案，未获所有者批准前不构成实施授权；所有开放问题（§8）需所有者拍板后才可排期。
>
> 起草：2026-10-05。上游锚点：[BLUEPRINT.md](../BLUEPRINT.md)（愿景与里程碑、web-client 演化定位）· [architecture.md](../architecture.md)（技术定案）· [ui-polish/rules.md](../ui-polish/rules.md)（UI 工艺规则现行源）· [CLAUDE.md](../../CLAUDE.md)（web-client 操作手册）。

---

## 0. 背景与现状（已核实，引用出处见括号）

**性能一期（wave1，2026-10-05 前后）已落地**（commits `02e66d0` → `34e4d02` → `0edc16b` → `7de802f` → `4322f91` → `f84da63`）：

- 黑洞场景（three.js ~640KB chunk + WebGL 初始化）延后挂载，最终形态为「首次交互揭示 + 8s 硬下限 setTimeout」（`f84da63` 修复了 `requestIdleCallback` timeout 语义误用）；
- 首页入场动画改 CSS 先行，LCP 摆脱 hydration 门控（`34e4d02`）；BGM 1.4MB WAV 与全局点击音效改手势加载（`02e66d0` / `4322f91`）；BGM 音量面板去 framer-motion（`7de802f`）；
- 实测收益（`02e66d0` 提交记录，本地 desktop）：TBT 11047ms → 1329ms（-88%），LCP 1239 → 1022ms，加载期 JS 传输 763KB → 325KB；Lighthouse Perf 39 → 55+（所有者给定口径）。

**剩余余量**：`f84da63` 提交记录指出移动模拟 TBT 仍 ~1040ms——three.js chunk（484KB）与 ~0.8s WebGL 初始化长任务仍落在揭示后的加载关键窗口。

**WASM 资源现状**：`public/godot/` 旧版 Godot 产物合计 ~51.5MB（`GoDot_game.wasm` 35.7MB + `GoDot_game.pck` 15.5MB + `GoDot_game.js` 281KB）；`next.config.ts` 仅对 `.gz` 变体设一年 immutable 缓存，**裸文件无 Cache-Control 配置**。`/arena` 经 iframe（`src="/godot/GoDot_game.html"`）挂载，守卫态（无战斗会话）不渲染 iframe（ui-polish AUDIT 守卫态审计可证）。

**UI 工艺底盘**：ui-polish 台账 R 序列现行（S5–S13 已归档），验证环境惯例为 build + `next start`（:4105）+ Chrome CDP；剩余队列含「首页黑洞画布 slow3G 首帧占位」等待办，与本 spec 的 CLS 专项直接相关。

**角色定位**（README 客户端矩阵 / CLAUDE.md / BLUEPRINT）：web-client 现役，随 client-godot-v2 推进**退化为官网 + Web 托管壳**，Arcade 保留作引流位；本 spec 的「内容化」服务于**社区运营与引流**，不是游戏本体功能——游戏本体一切玩法开发在 client-godot-v2 线。

---

## 1. 目标（一句话）

**性能二期**：在固定度量口径下把 Lighthouse 移动档 Perf 从 55+ 推到 **70+**，对 LCP / CLS 做专项治理，并给 51.5MB 旧版 WASM 资产立一套按需加载与缓存策略；**内容化**：新增开发日志 / 路线图 / 截图画廊 / 版本更新四个内容板块，让官网从「壳」变成玩家会回访的地方，为 Steam 首发蓄积社区势能。

---

## 2. 非目标（明确排除）

1. **backend（❄️ 一期封存）零改动**：不开发、不部署、不新增任何 API / 数据库 / 动态后端能力（评论、账号、订阅统统不做，内容化是纯静态方案）。
2. **client-godot（❄️ 冻结）与 client-godot-v2 零改动**：本 spec 不给两条线派任何活；画廊只「引用」美术产出文件，不改美术管线；不做「新 Web 试玩 demo」（v2 的 Web WASM 导出属于 v2 自己的里程碑）。
3. 不做全站 i18n（开发日志语言见开放问题 Q5）；不重设计 Arcade 小游戏本体；不动 `/arena` 对战逻辑与逃跑惩罚守卫。
4. 不以「升级依赖换性能」为主手段（three.js 0.161 → 新版本仅作为开放问题 Q8 评估，默认不做）。
5. 不追求波浪式重设计首页视觉——性能二期以 wave1「特效零删减」为同等纪律。

---

## 3. FR（功能需求）

### A 线：性能二期

- **A1 WASM 资源按需加载与缓存策略**（对应 `public/godot/` 51.5MB）：
  - 守卫态与首页对 `/godot/*` 的请求数必须为 0（现状守卫态已不渲染 iframe，需以网络面板实测固化）；
  - 明确「进入对局前是否预取」的策略决策：纯按需（点击进入才开始拉）vs intent 预取（守卫通过后 idle 预取 `.js` 引导文件）——预取只允许作用于小体积引导文件，51.5MB 主体永不预取；
  - 裸 `.wasm/.pck/.js` 补齐 `Cache-Control`（对齐 `.gz` 变体的一年 immutable 策略），并验证 `.gz` 与裸文件的命中路径不双拉；
  - 产出一份 WASM 加载时序记录（首次进入耗时、二次进入缓存命中耗时），作为后续 v2 Web demo 的策略输入。
- **A2 LCP 专项**：
  - 固定「每路由的 LCP 元素」认定（首页当前为 hero 文字区，CSS 先行后已与 hydration 解耦）；
  - 字体加载策略审计：`font-display` 行为、关键字体 preload / 子集化评估（黑洞揭示、lobby 标题均依赖自定义字体）；
  - 图片路径治理：内容化新增图片统一走 `next/image`，首页 / lobby 既有 `next/image` 使用点补 `priority` / `sizes` 审计。
- **A3 CLS 专项**（此前未专项测量）：
  - 全路由建立 CLS 基线；已知候选源：黑洞 8s 揭示 / 首次交互揭示、字体交换、lobby 弹层与头像挂载（ui-polish 剩余队列「slow3G 首帧占位」并入此项）；
  - 目标见 NFR；修复手段优先占位尺寸预留与 `preload`，不牺牲 wave1 的延迟挂载收益。
- **A4 TBT 余量**（移动端 ~1040ms）：
  - 剩余长任务源定位（three.js chunk 拆分评估、WebGL 初始化是否可再延后到 canvas 可见后、hydration 脚本量）；
  - lobby 仍整体依赖 framer-motion（与首页已去 framer 化对比），评估 lobby 动效瘦身的收益与风险。

### B 线：官网内容化

- **B1 内容数据约定**：内容即代码——MDX 或 JSON 单一来源（形态待 Q3），git 提交即发布，零后端零构建外依赖；内容文件与页面组件解耦，保证未来整体迁移成本最低（呼应「退化为托管壳」的演化方向）。
- **B2 四个内容板块**（路由名暂定，遵循现有 kebab-case 惯例）：
  - `/devlog` 开发日志：按时间倒序的日志列表 + 单篇详情页；
  - `/roadmap` 路线图：里程碑视图（数据源与 BLUEPRINT 的同步方式见 Q4）；
  - `/gallery` 截图画廊：网格 + 灯箱查看，支持标注「开发中 / WIP」水印；
  - `/changelog` 版本更新页：按版本号的更新条目。
- **B3 入口整合**：首页与 lobby 导航接入四个板块，不挤占现有主 CTA（登录 → 大厅）动线；Arcade 引流位保持。
- **B4 SEO 基础**：四页 metadata + OG 图、`sitemap` / `robots`（是否纳入待 Q 决策后定深度）。

---

## 4. NFR（非功能需求，可量化）

| 指标 | 门槛 | 口径 |
|---|---|---|
| Lighthouse Performance | **≥ 70**（当前 55+） | 移动档模拟（具体设备 / 网络档在 T0 固化，见 Q1/Q2） |
| LCP | 每路由 ≤ 2.5s（慢网档目标在 T0 基线后定档） | 同上 |
| CLS | 每路由 ≤ 0.05；内容四页 ≤ 0.02 | 同上 |
| TBT | desktop ≤ 300ms；移动档在 T0 基线上定降幅目标 | 同上 |
| 内容页自身预算 | 单页 JS 增量 ≤ 30KB（gz），LCP ≤ 2.0s（desktop） | 新增四页逐页测 |
| WASM 隔离 | 首页 + login + lobby + 守卫态 `/godot/*` 请求数 = 0 | 网络面板实测 |
| 缓存 | `/godot/*` 裸文件与 `.gz` 变体均返回长周期 `Cache-Control` | `curl -I` 验证 |
| 既有质量线 | ui-polish 扫描组合（a11y / 溢出矩阵 / interact）全绿不回退；`npm run build` / `lint` 绿 | 现有惯例 |
| 视觉纪律 | 黑洞与入场动效零删减（wave1 同等纪律） | 前后同相机截图对比 |

---

## 5. AC（验收标准）

1. **AC-性能**：T0 固化口径下产出 before/after 全路由性能报告（Lighthouse JSON + 截图留档），Perf / LCP / CLS / TBT 全部达 NFR 门槛；不达标项逐条给出根因分析与是否可达的结论（允许带证据申请降档，由所有者裁决）。
2. **AC-WASM**：真实浏览器走查证明首页 / lobby / login / arena 守卫态网络面板零 `/godot/` 请求；`curl -I` 证明缓存头生效；产出 WASM 加载时序记录一份。
3. **AC-内容**：四个板块真实页面走查通过，每板块至少 1 篇 / 1 项真实样例内容上线（非 lorem 占位）；移动端适配过 ui-polish 扫描器。
4. **AC-无回退**：ui-polish 既有全绿项复跑不回退；黑洞场景前后对比截图视觉无删减；`npm run build` / `npm run lint` 绿。
5. **AC-真实页面**：部署后线上真实页面抽查关键路由（本地分数 ≠ 线上验收，部署走 asterforge-deploy 既有流程，是否强制线上复测见 Q9）。

---

## 6. 任务分解草案（依赖序）

```
T0 度量口径固化 + before 基线（阻塞全部）
 ├── T1 LCP / CLS / TBT 专项攻坚（A2/A3/A4，可并行于 T2）
 ├── T2 WASM 按需加载与缓存策略（A1，可与 T1 并行）
 ├── T3 内容框架选型落地（B1，依赖 Q3 决策）
 │    └── T4 四板块页面 + 样例内容（B2，依赖 T3）
 │         └── T5 入口整合 + SEO 基础（B3/B4，依赖 T4）
 └── T6 终验：全量回归 + after 报告 + 线上复测（依赖 T1–T5 全部）
```

- **T0**：固定 Lighthouse 设备 / 网络档与工具链（本地 build+start :4105 惯例 + 是否叠加 PSI/WPT）；产出全路由 before 报告；CLS 首次专项基线。
- **T1**：按 A2 → A3 → A4 顺序（LCP 手段最明确先行；CLS 并入黑洞占位待办；TBT 最后因其可能涉及拆包）。
- **T2**：缓存头（小而确定）先行；预取策略决策与实测随后；产出时序记录。
- **T3–T5**：内容线独立推进，页面产出后立即纳入 T0 口径的性能预算测量。
- **T6**：全量回归 + 真实部署页面验证 + 台账回填（ui-polish AUDIT 追加本轮记录或本 spec 直接勾选）。

---

## 7. 风险

| # | 风险 | 缓解 |
|---|---|---|
| R1 | 移动档 + 慢网模拟下 70+ 受物理带宽制约，可能不可达 | T0 先出基线定可达性；允许带证据申请分档目标（Q1） |
| R2 | 内容化扩大 web-client 体量，与「退化为托管壳」的演化方向有张力 | B1 内容即数据约束，内容文件与组件解耦，可整体搬移 |
| R3 | 画廊 / OG 图素材依赖 M1 美术产出节奏（三角色返工进行中，素材未定稿） | 首版仅用 `asternova/assets/` 既有素材 + WIP 水印，边界见 Q7 |
| R4 | Next.js 16 与训练数据破坏性差异（AGENTS.md 强制警告）；`ignoreBuildErrors: true` 使 build 通过 ≠ 类型正确 | 实施前读 `node_modules/next/dist/docs/`；关键改动补 `tsc --noEmit` |
| R5 | 站点部署为本地 build + scp（asterforge-deploy 流程），本地性能分 ≠ 线上 | AC-5 强制线上抽查；是否全面线上复测见 Q9 |
| R6 | TBT 攻坚若走 three.js 拆包 / 升级，着色器与视觉回归风险大 | 拆包优先、升级默认不做（Q8）；任何动效改动走前后同相机截图对比 |

---

## 8. 开放问题（所有者决策点，批准前需逐条拍板）

- **Q1 目标口径**：Perf ≥ 70 按 Lighthouse 移动档还是分「移动 70 / 桌面 90+」双档？（草案倾向：以移动档为准，桌面档顺带记录不设门槛。）
- **Q2 验收工具**：本地 Lighthouse（build + start）为唯一门槛，还是 PSI / WPT 线上复测也纳入门槛？
- **Q3 内容形态**：MDX（日志/更新页富文本表达力强）vs JSON（路线图/画廊结构化）vs 混合（按板块分形态）？（草案倾向：混合——devlog/changelog 用 MDX，roadmap/gallery 用 JSON。）
- **Q4 路线图数据源**：与 BLUEPRINT 里程碑手工转译（发布视角可控、内部决策不曝光）vs 构建时直接引用（零同步成本但可能泄露未公布决策）？（草案倾向：手工转译 + 发布检查清单。）
- **Q5 开发日志语言**：中文 / 英文 / 双语？（涉及目标受众：Steam 首发面向的中文玩家社群还是国际visibility。）
- **Q6 旧版 WASM demo 去留**：51.5MB 的旧版试玩（`/arena` + asterforge.top/game）在 v2 逐步成势后是否保留引流位？若保留，本期只做缓存与按需加载；若倾向退役，A1 范围可裁剪。
- **Q7 画廊首版素材边界**：仅 `asternova/assets/` 既有图（压测图表 / 旧版截图）先行，还是等 M1 角色定稿图再开画廊？
- **Q8 three.js 0.161 升级**：是否纳入本期？（收益：包体与性能潜在改善；风险：黑洞着色器回归。草案倾向：不纳入。）
- **Q9 线上复测强度**：AC-5 的线上抽查是「关键路由人工走查」还是「全路由 Lighthouse 线上跑分」？

---

## 9. 批准记录

| 日期 | 决策人 | 结论 |
|---|---|---|
| — | — | 待所有者评审 |
