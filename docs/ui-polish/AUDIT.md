# UI Polish 审计台账（AUDIT）

> 永续循环目标：前端 UI 细节打磨（零人类参与）。每轮追加一节，最新在上。
> 截图与扫描 JSON 存临时目录：`.ui-polish/artifacts/`（不进仓库）；扫描器 `docs/ui-polish/tools/audit.mjs`。
> 站点：`http://127.0.0.1:4105`（`npm run build` + next start；dev server 因沙箱禁管道 stdio 不可用，见踩坑）。
> 审查浏览器：Chrome 153 headless + CDP（9333）。主题：深空黑单主题（无浅色态，不新增）。
> **轮次连续性**：R1–R4 台账历史上位于 `asternova/docs/ui-polish/AUDIT.md`（git 历史可查，工作树旧目录已删）；本台账从 **R5** 起接续编号，历史队列已合并至下方「剩余队列」。

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
