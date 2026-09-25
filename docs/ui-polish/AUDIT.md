# UI Polish 审计台账（AUDIT）

> 永续循环目标：前端 UI 细节打磨（零人类参与）。每轮追加一节，最新在上。
> 截图与扫描 JSON 存临时目录：`.ui-polish/artifacts/`（不进仓库）；扫描器 `docs/ui-polish/tools/audit.mjs`。
> 站点：`http://127.0.0.1:4105`（`npm run build` + next start；dev server 因沙箱禁管道 stdio 不可用，见踩坑）。
> 审查浏览器：Chrome 153 headless + CDP（9333）。主题：深空黑单主题（无浅色态，不新增）。
> **轮次连续性**：R1–R4 台账历史上位于 `asternova/docs/ui-polish/AUDIT.md`（git 历史可查，工作树旧目录已删）；本台账从 **R5** 起接续编号，历史队列已合并至下方「剩余队列」。

---

## R12（收尾轮）· 用户手动叫停 → 暂停打磨

### 隔轮评审（R11 改动）

- 死样式删除（gravity/pulse-scan）：全仓 grep 0 残留 + 本轮终态复扫通过 → **通过**。
- BGM 外环 ambient 令牌：计算样式 1.8s/2.6s 前后一致 → **通过，无 revert。**

### 未实施（因用户叫停，留作召回首项）

- `app/lobby/page.tsx:312-313` logo hover 旋摆 `duration: 0.5` 超 150–300ms 带 → 拟归 0.3s（WAAPI 取证脚本已备，临时目录）；规则依据 rules §6。
- 队列余项：sonner toast 时长语料、slow3G 首帧占位截图、xiaoxiaole SW 离线取证、弱网截图隔轮评审。

### 终态验证（本次收尾取证）

- 全量扫描 10 路由 × 双视口 = 20 组合：语义/布局/a11y/console **0 问题**（保留项不变：16×16 label checkbox、404 自身资源日志、merge 渐变按钮已裁定达标）。
- 最近全套记录：interact 33/33（R8）、edge 22/22（R9）、矩阵 tablet/wide/tiny 27 组合全绿（R9）。
- build/lint：基线 0 errors（1 条 R1 定案保留 warning）。

### Commits 累计

- 19 个 Conventional Commit（R5–R11）+ 本收尾台账提交，**全部已推送 origin/main 同步**。
- 站点与验证脚本、台账、规则文档全部入库；截图/扫描 JSON 存 `.ui-polish/artifacts`（不进仓库）。

### 结论

- 目标按用户指令暂停（永不停止条款的「手动叫停」出口）。环境（:4105 站点、CDP 浏览器、看护脚本）保持可用，随时可恢复继续 R12+。

---
## R11（本轮）· 轨 2 数据轮：死样式清理 + 恒等令牌化 + 深扫语料

### 隔轮评审（R10 改动）

- R10 光痕 0.88s→0.9s（--duration-slow）：计算样式复核 0.9s ✓；hover 截图对像素 diff 0.068%（局限在动画相位差，bbox 覆盖卡片行与黑洞画布，属环境动噪声非结构变化）→ **通过，无 revert。**

### 修复清单（轨 2）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 工艺·删繁就简 | `app/globals.css` | 死样式 2 处：`gravity-scan`（keyframes+class）、`pulse-scan`（keyframes）零组件引用 → 删除（rules 新增「死样式纪律」：无引用即删，删前 grep 取证） | 全仓 grep 0 残留；home 前后截图 diff 0.198%（黑洞画布动画噪声，结构零变化）；build ✓ |
| P2 | 工艺·恒等令牌 | `LoopingBgmControl.tsx` | BGM 外环提醒 ping `[animation-duration:2.6s]` 字面值 → `var(--duration-ambient)`（值恒等 2600ms，零视觉变化）；内环 1.8s 保留为差拍提醒环 | 计算样式前后均 1.8s/2.6s ✓ |
| P2 | 语料 | 数据采集 | login tabs 切换 transition 0.15s（150–300 带内），属性 color/bg/border/outline ✓；BGM 双环 1.8/2.6（保留差拍设计）；wide 第二行单卡左对齐栅格起点（723=gridLeft，正常网格流） | telemetry2 全部澄清 |

### 深扫（本轮轮空补偿项，全过）

- **超长文案注入**（120 字标题 + 120 字描述）：桌面卡高 319px / 移动 279px 纵向扩展，**双视口页面级横向溢出均为 0**，网格自适应完好。
- 回归扫描 4 路由 × 双视口 8/8 绿。

### 跳过 + 原因

- BGM 内环 1.8s 令牌化：双环差拍为既有提醒设计（无视觉评审模型可核验改动审美）→ 保留原样。
- 其余无。

### 保留 + 原因

- 见上（BGM 内环）；规则弹层 checkbox 等历史定案维持。

### 验证汇总

- build ✓ · lint：本项目触碰文件 0 errors（全仓仅历史保留 warning arena:173，本轮入口 exit-code 表现异常已隔离核实与改动无关）。
- 证据：`home-scan-before/after.png`、R10 hover 截图对（artifacts，不进仓库）。

### Commits（本仓库）

1. `style(web): 清理死样式 + BGM 提醒环挂 ambient 令牌 / remove dead styles, ambient-token the BGM ping ring`
2. `docs(ui-polish): R11 轨2数据轮台账与死样式纪律 / R11 craft-ledger and dead-style discipline`
- push 结果：正常。

### 剩余队列（R12+ 候选）

- [P2工艺] login 头像/logo hover 旋摆 0.5s 与 150–300 带的关系语料；Toaster(sonner) 入场时长语料。
- [P3] 弱网加载态截图评审（R9 已采证，转入隔轮评审材料）；首页黑洞画布在 slow3G 下的首帧占位样式。
- [P3] xiaoxiaole 内嵌页 service worker 缓存行为与 404 恢复路径取证。

### 踩坑（本轮）

1. 惯性操作：先给死样式做令牌化（gravity-scan 7s）→ grep 后发现元素已不存在（死类），随即改道为删除；令牌化前必须先验引用存在。
2. 一次成型脚本的括号计数目测不可靠 → 表达式写入前用平衡计数器+Function 编译双重校验（三次翻车后的规则）。
3. `[role=tab]` 语料首次在 lobby 采样为空 → 采样页面应为 login（数据页与断言页要一致）。

---

## R10（本轮）· 轨 2 工艺首轮：动效令牌归一 + 文案/排版语料采集

### 隔轮评审（R9 改动）

- R9 仅工具变更（web 零文件改动）；本轮回归扫描 6 路由 × 2 视口零回归，工具自愈续跑。**通过，无 revert。**
- 评审方式说明：本部署无视觉模型 → 轨 2 证据改用「计算样式前后值 + 同视口截图对 + 下轮数字复核」；本轮截图对已存 artifacts（见下）。

### 修复清单（轨 2 · 三件套齐全）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 工艺·动效令牌 | `app/globals.css` lobby 光痕 | `animation: lobby-enter-sheen 0.88s ease-out` 硬编码 → `var(--duration-slow)`（900ms，rules §6 既有「一次性装饰扫光」令牌） | 计算样式 0.88s → 0.9s；截图对 `lobby-hover-before/after.png`；hover 光晕/transition 值不变（0.3s 在 150–300 带内） |
| P2 | 工艺·规则补录 | `docs/ui-polish/rules.md` §6 | 无「一次性扫光」归属 → 补录：装饰扫光/电影感过渡挂 `--duration-slow` | — |

### 数据化语料（无码项，全数达标）

- **CTA 动词分布**（wide 采 2560）：进入×5 / 开始匹配 / 登录 / 返回大厅 / 知道了 / 开始任务 / 重新开始 —— 与 rules §6 动词清单一致，无近义动词散落。
- **大厅 wide 布局断言**：2560px 下 5 卡首行 4 卡（lg:grid-cols-4 生效），第 5 卡换行 —— 符合预期。
- **ResultOverlay 动效语料**（静态核查）：springSnappy / cinematicEase 双共享令牌 + closeOnEsc:false 语义，无裸 ease/时长散落。
- **hover 时序**：tile transition-duration 0.3s（150–300 带内 ✓）、呼吸 2.6s（--duration-ambient ✓）、光痕 0.9s（--duration-slow ✓）—— 三类动效三档令牌齐整。

### 跳过 + 原因

- 纯视觉审美项（饱和度/留白/字重微调）：无视觉评审模型可用，三件套 c 无法独立核验 → 依纪律跳过，不拍脑袋。

### 保留 + 原因

- `--duration-base: 500ms` 与 `--duration-slow` 邻接：用途分属「页面区块过渡」与「装饰扫光」，暂不变更层级（R2 已定）。光痕取 slow 是保守归一（0.88→0.9s 视觉近零差异）。
- 规则弹层 checkbox 等 R1 定案项维持。

### 验证汇总

- build ✓ · lint 基线 0 errors · 回归扫描 6 路由 × 双视口：landmark/溢出/跳档/重叠/console **0 回归**。
- 证据文件：`.ui-polish/artifacts/shots/lobby-hover-before.png` / `lobby-hover-after.png`（不进仓库）；计算样式前后值见上表。

### Commits（本仓库）

1. `style(web): 光痕时长归一 --duration-slow / normalize hover sheen to --duration-slow token`
2. `docs(ui-polish): R10 轨2首轮台账与规则补录`
- push 结果：本轮 push 正常（凭据恢复后的第二轮验证）。

### 剩余队列（R11+ 候选）

- [P2工艺] loopbgm ping 环（1.8s/2.6s 双频）入 ambient 令牌家族并一轮化。
- [P3] wide 档 5 卡换行留白比例断言（第 2 行单卡视觉重心）；loading 骨架/首帧截图评审。
- [P3] login 双 tab 切换动效时长语料（tabs transition 150ms?）。
- 待部署：同前。

### 踩坑（本轮）

- hover 态证据需真实指针：CDP Input.dispatchMouseEvent 悬停后取 :hover 匹配 + 光痕计算样式；直接 toggle class 无法触发 CSS :hover。
- wide 语料里 CTA 文本含卡片内部 span 文本，动词统计需按业务 CTA 元素级（span.enter-pill）采样，整卡 textContent 会混入标题。

---

## R9（本轮）· 视口矩阵 + 多档弱网 + 配方与网格节奏数据化

### 隔轮评审（R8 改动）

- R8 工具轮没有改 web 代码；整套件（扫描/interact/edge）复跑维持绿。**通过，无 revert。**

### 修复/新增清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P3 | 视口矩阵 | audit.mjs | 桌面/移动两档 → 增 tablet 768×1024 / wide 2560×1440 / tiny 320×568 | 9 路由 × 3 视口 = 27 组合全绿（仅保留项），横向溢出 0 |
| P3 | 弱网分档 | edge.mjs | 仅慢速 3G 档 → 增 3G(270ms/95KBps) 与 4G(60ms/366KBps) 档 | 新增 4/4 渲染完整（总 22/22） |
| P2 | 配方数据 | edge.mjs | login 重置弹层打开态未测 → 打开后实测：18px 圆角 / surface-2@90% / glass 边框 8% / blur40 / 430px / p-6 —— 与登录面自有 surface 变体一致 | 实测达标 |
| P2 | 网格节奏 | edge.mjs | 星象台 fine-grid 项长期挂队 → 数据化：首页主网格 64px 紫 0.07/青 0.05 线、登录细网格 24px 白 0.025 线 + 主网格降 0.6 透明度 —— 两级节奏为 R2 committed 决策，数值自洽 | 数据登记，保留设计 |
| P2 | 工具韧性 | audit/interact/edge | 浏览器掉线整轮报废 → 内建 CDP 健康计：死机按 R8 配方自动拉起并续跑 | 矩阵轮初即自愈续行，0 中断 |

### 跳过 + 原因

- 多语言（英文 locale）项：站点未做 i18n（单一 zh-CN），无英文版路由可测；新增 i18n 属新功能，默认禁止 → 关闭项并记录（title 模板联动已在每路由中文标题下持续验证）。
- push：本会话无凭据（SEC_E_NO_CREDENTIALS）×3 → 留本地。

### 保留 + 原因

- 规则弹层 16×16 checkbox（仍 6 处扫描 small=1）：R1 定案。
- merge 渐变按钮对比度：本轮矩阵三视口复核（知道了 7、再来一局 postModal 5.0–6.9）继续通过，非缺陷。
- nebula pausedUpgrade / ResultOverlay 配方语料：需真实对局中途状态，无后端的本地环境不可达 → 语料采集转为「设计插图态补充」待后端可跑时再录。

### 验证汇总

- web 侧零文件变更：build/lint 无需重跑（基线 0 errors）。
- audit：桌面/移动 20 组合 + 矩阵 27 组合全部绿。
- interact 33/33（R8 建）。edge 22/22。

### Commits（本仓库，累计 14 个本地提交未推送）

1. `待提交 test(ui-polish): 视口矩阵与多档弱网、配方与网格数据采集、浏览器自愈`
- push 结果：无凭据失败，留本地。

### 剩余队列（R10+ 候选）

- [P2] 工艺轮（轨 2 首轮）：细网格透明度节奏本作「保留」定案 → 转排 unlike 项：剩 lobby 卡片 hover 光晕 group-hover 版本时长数据化；星爆/结算 ResultOverlay 动效时长入令牌语料。
- [P3] 大视口行列：wide 档下 lobby 卡片 4 列换行与 hero 字号上限断言（本轮 wide 仅断言溢出，未断言孪生排布）。
- [P3] 弱网加载态截图证据（扫描 json 已含截图，属待下轮隔轮评审用）。
- 待部署：同前（无无人值守部署文档）。

### 踩坑（本轮）

1. 像素采样点落在视口外（tablet 底部工具栏半出视口）→ 采样坐标按「可视区裁剪」重算，避免截图边界夹取假数据。
2. 弹层遮挡判定一度被全屏 wrapper 矩形误导（几何判定把压在弹层下的元素误认作弹层自身）→ 改 DOM 祖先级 inDialogEl 判定，几何仅作旧数据回退。
3. 浏览器掉线造成整轮报废 → 三工具内建自愈；矩阵轮当场验证自愈路径（首行失败 → 拉起 → 27 组合全绿）。
4. grouping 断言失误（fine-grid 实际在登录页而非常规首页）→ 探针改为分页采集粗/细网格，数据才具可比性。

---

## R8（本轮）· 全路由键盘轮转 + 边界数据深扫 + 配方测量闭环

### 隔轮评审（R7 改动）

- R7 修复（消消乐 label、ambient 令牌）与既有战线复验：全量扫描 + interact 33/33 + edge 15/15 全绿。**通过，无 revert。**

### 修复/新增清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 键盘 | `docs/ui-polish/tools/interact.mjs` | 仅 login/弹层场景 → 五页面（home/login/lobby/xiaoxiaole/404）Tab 环轮转：首选=skip link、环内全部落点可见、页内无名可见按钮=0（×3 断言/页）；落点身份改坐标+文本+aria 闭环 | 33/33 全绿 |
| P3 | 弱网 | `docs/ui-polish/tools/edge.mjs`（新增） | 无弱网覆盖 → CDP 节流（150kbps/700ms）五路由渲染完整性（h1=1 + 横向溢出 0） | 5/5 渲染完整 |
| P3 | 离线 | edge.mjs | 无取证 → 离线加载呈现浏览器默认错误页（本站无离线壳/SW 属设计内情况，取证登记） | 记录保留 |
| P3 | 极端数据 | edge.mjs | 无 → 80 字 CJK+emoji 昵称种子进大厅：头部 span ellipsis 截断、无页面级溢出 | PASS |
| P2 | 配方核对 | edge.mjs | 「弹层容器配方逐页核对」入队 → 双视口实测：merge/nebula 规则弹层 = 桌面 32px 全圆角/420px/glass 4%+8%/blur40/p-6，移动 28px 顶圆角底抽屉/p-4，与 rules §4 完全一致；star 保留居中全圆角变体（§4 允许） | 实测达标，无需改码 |
| P2 | 工具稳定性 | audit/interact/edge + `ensure-chrome.ps1`（新增） | 多轮累计未关闭标签致浏览器崩溃 + 沙箱收紧后 AppData 写被拒（Chromium crashpad 直接退出）→ 统一 Target.closeTarget 关标签；看护脚本以「Crashpad 禁用 + 工作区 profile」配方拉起，CDP 掉线自愈 | 连续特训稳定跑完三套件 |

### 跳过 + 原因

- 弹层配方仅在「打开态」可测：login 重置弹层初始关闭 → 留待 push 前补测（低级，不影响验收口径，已在 R3/登深扫中人工复核过其玻璃工艺）。
- push：本会话无凭据（SEC_E_NO_CREDENTIALS）×3 → 留本地。

### 保留 + 原因

- 规则弹层 16×16 checkbox（6 扫描 small=1）：整行 label + 原生尺寸，R1 定案保留。
- 离线无自定义断网页：无离线壳是产品定位（深空大厅要求在线）；新增 SW/offline 页属「新增花活+运行时依赖」，默认禁止。
- 慢网下首屏依赖字体/分块（自托管 next/font，可缓存）：弱网渲染完整性已实测达标。

### 验证汇总

- build 无改动（纯工具轮；web 侧零文件变更）· lint 基线 0 errors。
- audit 全量扫描：main/skip/h1/未标签/溢出/重叠/截断/console 全绿（仅保留项）。
- interact：**33/33**。edge：**15/15**。
- 浏览器后端随笔：Chrome→Edge（Chromium 153 同 CDP 协议），配方入 ensure-chrome.ps1。

### Commits（本仓库，累计 12 个本地提交未推送）

1. `caf91be test(ui-polish): 边界扫描器、全路由 Tab 环与浏览器看护脚本`
2. （历史 11 个见前轮台账）
- push 结果：无凭据失败，留本地。

### 剩余队列（R9+ 候选）

- [P2] lobby/arena 深度可达状态走查（带真实后端 or 更深种子）；login 重置弹层打开态配方补测。
- [P2] 工艺轮：星象台 fine-grid 透明度节奏数据化复核（本轮未及）；nebula pausedUpgrade 弹层与 ResultOverlay 分支的配方语料并入 edge 配方表。
- [P3] 更多视口矩阵（768×1024 / 2560×1440 / 极小 320×568）复用现扫描器跑一遍；弱网矩阵加 3G/4G 档与图片延迟对 404 页影响。
- [P3] 多语言标题（英文 locale）与文档 title 模板联动检查。

### 踩坑（本轮）

1. **沙箱收紧：AppData Local 写入被拒** → Chromium crashpad 写 throttle_store.dat 即退出（Chrome/Edge 同因）；配方 `--disable-features=Crashpad` + 工作区 user-data-dir 解决；网络沙箱 ACL grant 报错为非致命噪声。
2. **标签泄漏导致浏览器崩溃**：历轮脚本只关 WS 不关标签，几百轮后 Chrome 崩 → 三工具统一 closeTarget；显见崩溃后必须先清 profile 锁再拉起。
3. **并行工具运行造成键事件丢包**（interact lobby-avatar Esc 偶发失败）：两个 CDP 套件严禁并发，全部串行（已固化接管流程）。
4. 仓库外部进程周期性跑 git（art/model 文件）→ 偶发 index.lock；提交遇锁只等重试，禁止强删锁。
5. 首轮「环内落点不可见」误报：skip link 聚焦后 200ms translate 入场未完成即测量 → 落点判定加 280ms 就位等待；BODY 落点为环耗尽终点而非违规。

---

## R7（本轮）· 对比度评估盲区闭环 + 内嵌游戏审计 + 工艺令牌

### 隔轮评审（R6 改动）

- R6 出壳/陷阱改动经 interact 全量重跑 + 全路由复扫：**18/18 与全指标维持绿，无 revert。**
- 新评审能力：扫描器新增弹层收起后的「二遍审计」（postModal pass），开局弹层下的底层真实 UI（工具栏/结算/暂停钮）纳入覆盖。

### 修复清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 工具·对比度 | `docs/ui-polish/tools/audit.mjs` | 渐变底无法判定（merge「再来一局/知道了」长期挂 1.0 比值 → 像素级复核：零依赖 PNG 解码 + 元素四角内缩采样 + 弹层遮挡判定 | 「知道了」采样 6.5–7.1:1 ✓；「再来一局」被弹层盖住时自动 exempt，关层后采样 4.1–4.7:1（字形区 ≥4.5）✓ —— **裁定均达标，item 关闭** |
| P2 | 模板 | `public/xiaoxiaole/index.html` | 设置面板「音量/特效质量」span 未关联 → `<label for>` | 内嵌页扫描 unlabeled 2 → **0** |
| P2 | 工艺·令牌 | `app/globals.css` | 大厅卡片呼吸 2.6s 硬编码 → `--duration-ambient: 2600ms` 令牌 + var() 挂接；rules.md §6 补录「氛围循环动效统一 ambient/禁用亚秒闪烁」 | computed `animation-duration=2.6s` 前后一致，零视觉变化 |
| P2 | 审计·覆盖 | audit.mjs | 内嵌游戏页（/xiaoxiaole/index.html 同源静态页）未审计 → 直接纳入扫描目标；开局弹层遮挡状态 → postModal 二遍审计 | 内嵌页 0 违规（详见保留）；games 三路由 postModal 均绿 |
| P3 | 工具 | interact.mjs | Tab 落点按签名去重（多空输入塌缩为 4）→ 坐标+文本+aria 身份闭环检测 | login 重置环 7 落点、头像环 11 落点、规则弹层 2 落点，全部准确 |

### 跳过 + 原因

- push：本会话无凭据（`SEC_E_NO_CREDENTIALS`）×3 退避失败 → 提交留本地，不碰凭据。
- /arena 深层战场：仍无真实会话（后端一期封存）。

### 保留 + 原因

- 规则弹层 16×16 checkbox（6 处扫描 small=1）：整行 label 包裹 + 原生尺寸，R1 定案，保留。
- 内嵌消消乐页无 skip link：单页无前置导航横幅，H1 即首内容（对齐 R1「无前置导航不强行加 landmark」原则），保留。
- 桌面「再来一局」采样含 4.1 角落点：为按钮外缘阴影/贴边像素，字形居中区 ≥4.5，裁定通过并记录。

### 验证汇总

- build ✓（token 改动后重建）· lint 0 errors · 全量扫描 22 组合（10 路由 + 内嵌页 ×2 视口）：横向溢出/重叠/截断/跳档/无标签全 0；console 仅 404 路由预期项；对比度经像素复核全达标。
- interact：**18/18**（含闭环身份检测）。
- `--duration-ambient` 计算样式复核 = 2.6s（前后一致）。

### Commits（本仓库，累计 10 个本地提交未推送）

1. `00997bf fix(web): 消消乐设置面板 label 关联`
2. `f227168 style(web): 氛围呼吸动效时长令牌化`
3. `8c5c2b1 test(ui-polish): 像素级对比复核与弹层后状态二遍审计、Tab 闭环检测`
4. （R5/R6 累计 7 个）
- push 结果：3 次重试 `SEC_E_NO_CREDENTIALS` → 留本地。

### 剩余队列（R8+ 候选）

- [P2] 工艺轮：星象台 fine-grid 透明度节奏复核；弹层容器配方逐页核对（rules §4 桌面三星游戏变体）。
- [P2] Tab 环全路由轮转脚本化（现仅 login/弹层场景），接入每轮扫描。
- [P3] 弱网（CDP 节流）/超长用户名/emoji/极端分数边界深扫。
- [P3] nebula briefing 的 Esc 语义已验（保持打开），「开始任务」后暂停态的 Esc/陷阱补一例；ResultOverlay 族其余分支核查。
- 待部署：本项目为本地/仓库内开发站点，无无人值守部署文档 → 记「待部署」。

### 踩坑（本轮）

1. 像素采样被开局弹层遮罩污染（桌面采样 1.2 的假阴性）→ verifyPixels 增加弹层矩形遮挡判定 + postModal 二遍审计；移动端因 R6「弹层打开即隐藏 chrome」直接规避。
2. Tab 落点重名塌缩（4 个空输入共用一个签名）→ 身份键补 left 坐标；首循环检测需容差防网格头重像替身（容差 ±3px 仍有局限，记录）。
3. 内嵌游戏为公有静态页：public/** 被 eslint 忽略仅因「非手写源码」惯例，但 xiaoxiaole 系手写（game.js/styles.css/index.html），其模板/CSS 层在可改范围——本轮只动了 index.html 标签关联，game.js（业务逻辑）不动。

---

## R6（本轮）· 移动端缩放壳读治理 + 键盘端到端闭环

### 隔轮评审（R5 改动）

- R5 全部改动在真实浏览器键鼠下复验：头像弹层（R5 新接 useDialogA11y）打开聚焦、Tab 陷阱、Esc 关闭通过；游戏壳 skip link / 返回钮 / landmark 维持全绿（全量复扫）。**通过，无 revert。**
- 评审手段升级：新增 `docs/ui-polish/tools/interact.mjs`（CDP 真实键鼠 e2e），替代 R1–R4 的「逻辑级验证」，历史遗留 `[P1] Esc/Tab 端到端复验` 一并在本轮闭环。

### 修复清单（批次一，即时复验）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 触控 | `src/components/game-shell/StagePortal.tsx`（新增） | 无共享方案 → 共享 portal 组件（SSR 首帧内联防 hydration mismatch，effect 后挂 document.body） | lint 0；三游戏弹层出壳生效 |
| P1 | 触控 | merge/nebula/star-dash（MergeGame/NebulaSurvivorGame/StarDashGame） | 规则弹层、GameOver、升级三选一全在缩放壳内（按钮实测 11–19px）→ 全部出壳；「知道了/开始任务/继续游戏/重新开始」实测 **44–51px**（前 14–19px）；移动端返回钮 floating 变体、暂停/规则 44×44、再来一局底部 44×44 | 扫描 small 数 8+ → **0**（仅剩 16×16 checkbox 见保留）；interact 首落点 inside-dialog 且按钮 h=51 |
| P1 | 触控 | `LoopingBgmControl.tsx` | 无 portal + 弹层打开时压住弹层 CTA（merge/nebula 扫描 0.61–0.64 重叠）→ portal + `hidden`（弹层打开即隐藏）+ `elevated` | 重叠 2+1 → **0** |
| P1 | 键盘 | `src/hooks/useDialogA11y.ts` | 闭包捕获一次性 root：弹层经 portal 搬运后 root 失联，焦点陷阱静默失效（实测焦点逃逸到 skip link）→ 每键实时解析 ref、isConnected 检查、不可聚焦时 60ms×20 重试聚焦 | interact：5 组弹层 Tab 陷阱全部 越界=0；Esc 语义全对 |
| P1 | 键盘 | 五弹层 e2e | R1–R4 仅逻辑级 → login-reset / lobby-avatar / merge / nebula-briefing（Esc 不关闭，语义正确）/ star-dash 全部真实键鼠 PASS（18/18） | `interact-summary.json` |
| P2 | 工具 | audit.mjs | 伪元素扩区豁免在缩放上下文误用 → 累计 transform 缩放检测（scale<0.9 标记）；fixed 层与滚动内容重叠豁免 | 本轮复扫全部归零 |

### 跳过 + 原因

- 渐变底对比度像素级验证器（PNG 采样）：时间盒内未及，merge 两处「黑字」经手工核算 ≈5.6:1+ 为扫描器盲区，继续排队。
- /arena 深层战场 HUD：仍需真实对战会话（无后端），守卫态正常。
- push：本会话无凭据（`SEC_E_NO_CREDENTIALS`）×3 指数退避失败 → 提交留本地；不碰凭据（红线）。

### 保留 + 原因

- 规则弹层 16×16 checkbox：scale=1 原生尺寸 + 整行 `<label>` 包裹（有效目标 ≥40px，R1 已定案），保留。
- 游戏内玩法控件（星爆/跳跃/滑铲/摇杆）随画布缩放：属游戏载体而非 chrome（rules §3 针对交互 chrome），保留。
- `arena/page.tsx:173` exhaustive-deps warning：涉守卫时序（R1 定案），保留。
- 桌面视图 chrome 维持原位（无缩放问题，portal 仅移动端路径复用同一弹层出口）。

### 验证汇总

- `npm run build` ×3 全绿（每次修复重建）· `npm run lint` 0 errors 1 warning（保留项）。
- `npx tsc --noEmit`：**本任务触碰文件 0 错误**；全仓 23 个存量类型错误均在未触碰文件（core-defense 遗留模块/StarFieldBg/OrientationLockType 等，基线即如此，rules §7 既有认知）。
- 全量扫描（20 组合）：横向溢出 0 · 重叠 0 · 截断 0 · 跳档 0 · 无标签控件 0 · console 0（404 路由仅预期项）· main/skip/h1 全达标 · 小目标仅存保留项。
- interact.mjs：**18/18 PASS**。

### Commits（本仓库，累计 6 个本地提交未推送）

1. `dd6d73e fix(a11y): 移动端游戏 chrome 出缩放壳 + 弹层焦点陷阱 portal 免疫`（6 文件）
2. `c9e28f5 test(ui-polish): 键鼠端到端验证器与缩放感知扫描器`（2 文件）
3. （R5 累计：80c1649 / 09742e2 / 91f6cc4 / ca2f956）
- push 结果：3 次重试均 `SEC_E_NO_CREDENTIALS` 失败 → 留本地待凭据（本轮与上轮同因）。

### 剩余队列（R7+ 候选）

- [P1] merge 渐变底对比度像素级验证器（PNG 解码采样，消除评估盲区并推广到全站）。
- [P2] iframe 壳内部 a11y（xiaoxiaole 同源页可注入审计；arena Godot 跨域仅外围）。
- [P2] 工艺轮：lobby 卡片光晕呼吸 2.6s 入 token；星象台 fine-grid 透明度节奏；弹层容器配方逐页核对（rules §4）。
- [P3] Tab 环落点按元素身份去重（现按签名去重，多空输入框会塌缩）；暂停态弹层 trap 专项。
- [P3] 弱网（CDP 节流）/超长用户名/emoji 昵称/极端分数边界深扫。
- [P3] ResultOverlay 族（merge GameOver 已在列外）nebula/nova-ball 分支核查。

### 踩坑（本轮）

1. **portal 迁移绕过了 useDialogA11y 的闭包 root**：首帧内联（防 hydration mismatch）→ effect 后迁 body，旧 hook 实例持有的 root 失联，陷阱静默失效且「首帧 display:none 不可聚焦」→ 修复为每键实时解析 + 重试聚焦；interact 工具在真实键鼠下成功复现（R1–R4 IAB 环境无法复现的正是此类）。
2. **程序化 `el.click()` 不移动焦点**：焦点归还断言需先 `focus()` 再 `click()` 模拟真实用户（interact 已修正）。
3. **AnimatePresence exit 保留 DOM 200–400ms**：Esc 断言需轮询至 2s，此前后 400ms 判定误报「未关闭」。
4. 仓库有并发 git 写者（`.git/index.lock` 瞬时冲突 + art/*.glb 被外部进程改动）：提交一律显式路径 add，绝不 `git add -A`。
5. Chrome headless 对个別 mp3 偶发 `ERR_CACHE_OPERATION_NOT_SUPPORTED`（range+compression 交互），非站点缺陷，console 计数豁免。

---

## R5（本轮）· 全路由硬验证基线重建 + 批次一修复

### 隔轮评审（R4/R3 改动）

- R4 本轮无代码改动，无评审对象。
- R3「404 SIGNAL LOST → font-mono-data」与 R4 后提交 8d3eeaa「404 CTA 箭头 lucide 统一」：本轮扫描 404 路由标题/landmark/对比度/console 均干净（唯一 console 记录为 404 资源本身，属预期）→ **通过，无 revert**。

### 修复清单（批次一，全部即时复验）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P0 | 工程 | `asternova/web-client/next.config.ts` | build 因沙箱禁 pipe stdio 在 page-data fork 处 EPERM → 增 `experimental.workerThreads: true` | build 全绿（exit 0，11 workers 线程模式） |
| P1 | 语义 | `src/components/game-shell/MobileLandscapeGameShell.tsx` | 四游戏路由（shoot/lets/merge/nebula）main=false、skip-link 目标缺失 → 双分支包裹 `<main id="main-content" tabIndex={-1}>` | 扫描 main=true ×4、skip.targetExists=true ×4（推翻 R1「壳不加 landmark」保留项，理由见 rules §5） |
| P1 | 语义 | `app/xiaoxiaole/page.tsx` | 容器 div 无 landmark → main#main-content | 扫描 main=true、skip=true |
| P1 | 语义 | `app/lobby/page.tsx` | h1=0（标题从 h2 起）、main 无 id（skip 落点缺失）→ sr-only h1 + main 补 id/tabIndex | h1=1、skipOk=true（桌面/移动均 ✓） |
| P0 | 键盘 | `src/components/shoot-them-all/render/StaPixiApp.ts` + `StaRoot.tsx` | Pixi v8 默认注入 1×1 离屏可聚焦「select to enable accessibility」占位按钮 → destroy + title/aria-label 双匹配清理 + MutationObserver 兜底 | 扫描 small=1 → 0（初版只匹配 aria-label 漏杀，坑见下） |
| P1 | 弹层 | `src/components/lobby/LobbyAvatars.tsx` | 头像选择弹层无 Esc/无焦点陷阱 → 接 `useDialogA11y` | lint 0 errors；与登录重置弹层同款 hook |
| P2 | 触控 | `src/components/audio/LoopingBgmControl.tsx` + lobby 使用处 | 大厅 BGM 控制条（z-120）压在底部固定「开始匹配」Dock（z 见下）右缘，遮挡约 32px 点击区 → 新增 `elevated` prop 上移至 Dock 之上 | 扫描 lobby-mobile overlaps 消失（配合扫描器 fixed 层判定） |
| P2 | 工具 | `docs/ui-polish/tools/audit.mjs`（+ .ui-polish 副本） | 三处误报：sr-only 截断、祖先/后代重叠、包 label 的 checkbox → 修正；新增 fixed-层与静态内容重叠豁免、离屏节点豁免、小目标 html 取证字段 | 复扫 0 误报 |

### 跳过 + 原因（铁律）

- **/arena 深层战场 HUD**：进入需要真实对战会话（守卫逻辑），本地无后端可复用；仅审计守卫态「战斗舱未解锁」+ 跳转行为（P 记队）。
- **浅色主题**：单主题设计，无需扫描。
- **推送失败**：`git push` 3 次退避重试均 `schannel SEC_E_NO_CREDENTIALS`（本会话无可用凭据）→ 提交留本地（80c1649 / 09742e2 / 91f6cc4 / 后续 docs 提交），待凭据可用后推送；不动任何凭据（红线）。
- **升级沙箱权限跑 next dev**：铁律零提问 + fail-closed 审批 → 弃，改用 build+start 等价路径。

### 保留 + 原因

- merge「再来一局」「知道了」近黑字：实为 rose→amber→teal 浅渐变底 + `text-gray-950`，手工核算对比 ≈5.6:1+（扫描器不支持渐变底 → 像素级验证器入队）；设计有意为之，非缺陷。
- 规则弹层 16×16 checkbox：整行 `<label>` 包裹（有效目标 ≥40px），扫描器已接受包裹 label，保留。
- login「返回首页」「忘记密码？」视觉盒 17px：伪元素扩区 45px（R1 已修），扫描器 p称伪元素后不再误报，保留。
- 大厅固定底 Dock 覆盖滚动中部卡片内容：移动端固定 Dock 的既定交互模式（内容滚过 Dock 属预期），保留。
- `arena/page.tsx:173` exhaustive-deps warning：补依赖改守卫时序，涉业务逻辑，保留（R1 同）。
- 404 路由 console 1 条「Failed to load resource 404」：404 页面本身的资源状态码记录，预期。

### 验证汇总

- `npm run build` 全绿 ×4（每次修复后重建）· `npm run lint` 0 errors 1 warning（保留项）。
- 全量扫描 ×3 + 定点复扫：20 组合（10 路由 × 桌面 1440×900 / 移动 375×812）。
  - 前 → 后：main landmark 缺失 ×6 路由 → 0；skip 落点缺失 ×7 → 0；h1 缺失（lobby）→ 0；unnamed icon buttons 0；unlabeled controls 0（修正包裹 label 误报）；heading 跳档 0；截断 0（sr-only 豁免后）；重叠 0（fixed 层豁免 + BGM 上移后）；console 错误 0（404 路由仅预期项）；横向溢出 0；title 唯一性 10/10。
  - 遗留：移动端「缩放壳内 HUD 目标过小」（merge/nebula/lets-running 的规则弹层按钮、BGM、暂停/规则按钮，视口内 7–19px）——R6 主攻（规则依据 rules §3 既有条款）。
- 视觉评审：本部署无图像能力模型（glm-5.2/5.3 read_image 均报不支持）→ 截图证据已按三件套存留，视觉复核改由 DOM/像素级脚本执行（像素验证器入队）。

### Commits（本仓库，已提交未推送）

1. `80c1649 fix(a11y): 游戏页 landmark/焦点陷阱/移动 Dock 重叠整治`（7 文件）
2. `09742e2 chore(web-client): 构建启用 experimental.workerThreads 兼容禁管道沙箱`（1 文件）
3. `91f6cc4 docs(ui-polish): 首轮审计记录、工艺规则与零依赖验证脚本`（3 文件）
4. 本轮 docs 补全提交（AUDIT R5 台账 + rules 合并历史）

### 剩余队列（R6+ 候选，含历史队列合并）

- [P1] 移动端缩放壳内交互控件外提（merge/nebula/lets-running：规则弹层、BGM、暂停/规则钮、结算弹层）——portal 出 ScaleFitGameStage 或 floating 变体（rules §3 既有条款）。
- [P1] login 重置弹层 / merge / nebula / star-dash / 头像弹层 Esc+Tab 端到端复验（Chrome CDP Input.dispatchKeyEvent 能力已具备，补 Tab 环扫描器 v2）。
- [P1] 渐变底对比度像素级验证器（PNG 解码采样）——消 merge 两处评估盲区。
- [P2] iframe 壳内部 a11y（xiaoxiaole /public/xiaoxiaole/index.html 同源可注入审计；arena 内 Godot 跨域仅限外围）。
- [P2] 工艺轮：lobby 卡片光晕呼吸 2.6s 时长入 token；星象台 fine-grid 透明度节奏。
- [P3] 弱网（CDP 节流）/超长用户名/emoji 昵称/极端分数/断网走势边界深扫。
- [P3] ResultOverlay 族（merge Game Over 等）焦点陷阱覆盖核查。

### 踩坑（本轮）

1. **禁管道 stdio**：`next dev` 与 build page-data fork 全 EPERM；workerThreads 线程模式通过（见 P0 行）。HMR 不可用，验证=重建+重启，端口 4105。
2. **端口影子**：3000/3100 被宿主机上他人进程占用且沙箱内 Get-NetTCPConnection 不可见 → 选 4105 并显式 -H 127.0.0.1。
3. **Pixi a11y 占位按钮 title 而非 aria-label**：首轮清理按 aria-label 匹配漏杀；扫描器 small 记录加 html 字段后定位。事件序：节点仅随扫描触发面出现概率化，最终以 selector 双匹配 + MutationObserver 兜底确定消除。
4. **模型无图像输入**：主模型与 glm-5.2/5.3 子代理均不能 read_image → 视觉评审降级为脚本判定 + 截图文档留档；像素级验证器入队。
5. 无头 Chrome 偶发崩溃（profile 锁）→ 重启时清 `.ui-polish/chrome-profile`。
6. 头显 Chrome 对个別 mp3 偶发 `ERR_CACHE_OPERATION_NOT_SUPPORTED`（range+compression），非站点缺陷，不计 console 错误。

---

## 历史轮次摘要（R1–R4，详情见 git 历史 `asternova/docs/ui-polish/AUDIT.md`）

- **R1（2026-09-24）全量基线**：主题锁定 forcedTheme=dark；全站 skip link；home/404/login/arena 补 main#main-content；arena 守卫空态；新增 useDialogA11y hook 并接线四处弹层；关键路径 44px 伪元素扩区（login/GameBackButton/shoot floating 返回钮出缩放壳）；xiaoxiaole sr-only h1、merge 双 h1 降级、游客输入 aria-label；lint 归零（public/** 忽略）。
- **R2**：ResultOverlay 接 useDialogA11y（closeOnEsc:false）；8 路由 × 320/700、812×375、2560×1440 溢出矩阵全 0。
- **R3**：登录深扫（空表单/401/209 字符超长输入/Tab 顺序）；404 SIGNAL LOST 换 font-mono-data。
- **R4**：平板 768×1024、1024×768、900×900 × 8 路由扫描（溢出全 0）；无修复轮。
- 历史环境备注：R1–R4 用 IAB 浏览器（rAF/焦点/CUA 键盘事件受限，Esc/Tab 仅逻辑级验证）——R5 起已换 Chrome CDP 真实浏览器，历史「逻辑级验证」项目可端到端复验（见剩余队列）。
