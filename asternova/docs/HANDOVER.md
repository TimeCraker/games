# AsterNova 主脑接手全景简报（Master Agent Handover Briefing）

> **生成时间**：2026-09-06  
> **文档定位**：供接手【主控主脑 / 首席架构师】角色的新 Agent 全盘掌握项目背景、核心技术定案、当前实战现状与未来实施路线的**交接宪章**。  
> **【强制前置要求】**：**接手前必须完整通读本文及下方列出的核心技术文档，严禁未读文档盲目推演或擅自修改既有架构！**

---

## 零、 必读核心技术文档清单（Mandatory Reading Order）

新主脑 Agent 在执行任何动作前，**必须按顺序阅读以下文档**（已全部完成内容与结构审计，与当前工程 100% 一致）：

1. **[`docs/BLUEPRINT.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/BLUEPRINT.md)**：项目最高愿景、四大里程碑（M0~M4）、单机优先+房主联机定案、战斗北极星（爽感与上瘾性）。
2. **[`docs/STYLE.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/STYLE.md)**：美术风格圣经。十六进制色板、终末地冷峻光照参数、三档画质规范、43 骨 Humanoid 架构、佩刀「星霜月华」规范。
3. **[`docs/architecture.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/architecture.md)**：技术架构总览。Forward+ 渲染器、AgX 色彩科学、双管线分工、GDScript 模拟核心、房主权威与分层预测。
4. **[`docs/pipeline/modular_art_and_asset_production_sop.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/pipeline/modular_art_and_asset_production_sop.md)**：场景与道具核心 SOP。四级资产架构（Tier 1~4）、**「AI 底模 + 自动化几何手术修补（Surgery & Modular Enhancement）」**工业管线。
5. **[`docs/pipeline/character-modeling-pipeline.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/pipeline/character-modeling-pipeline.md)**：角色 3D 工业制作 SOP。8.5 头身、SDF 面部解耦、内凹星空眼、面数预算。
6. **[`docs/pipeline/weapon-modeling-pipeline.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/docs/pipeline/weapon-modeling-pipeline.md)**：武器与硬表面建模 SOP。800~1,500 面、刀身与刀鞘双分件零偏置。
7. **[`AGENTS.md`](file:///c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/AGENTS.md)**：本地 CLI/MCP 双模规范、沙盒隔离目录纪律、严禁虚假量化自嗨。

---

## 一、 项目背景与历史重大纠偏（Pivots & Lessons Learned）

### 1. 核心定位与用户画像
- **制作人**：TimeCraker（Huanrui Zhang），商业化导向的独立全栈架构师。
- **项目定位**：二次元高速 3D 动作 RPG（Steam 端游首发，单机为主 + 2~6 人房主联机开黑），对标《明日方舟：终末地》的冷峻通透质感与《鬼泣》《Apex》的高机动战斗爽感。
- **生产方式**：主脑负责全局调度、架构把关与代码编写；并行 Agent 负责单点建模与贴图；用户负责审美把关与玩法决策。

### 2. 五大历史重大纠偏（前车之鉴，坚决不可重蹈覆辙）
1. **架构翻转（去中心化）**：
   - 早期试图自建中心服务器，开发负担沉重。已果断翻转为**「单机为主 + 房主权威开黑（Steam Networking Valve 免费中继）」**，Go 后端全部基建封存为二期大型联机资产。
2. **渲染底座彻底升级（告别 Compatibility 妥协）**：
   - 早期为了 Web demo 选用 `gl_compatibility`，导致片元缺少 Clustered 光照，出现 2.88x 强光异常，逼迫写 `diffuse_scale = 0.20` 等变态 hack，且无 SSAO、SSR 与探针。
   - **已正式拍板全面升级为 Forward+ (Vulkan Clustered) + AgX 色彩科学（模式 4）**，PC 默认解锁高刷（120+ FPS 起步上不封顶）。
3. **审美标杆确立（拥抱终末地，坚决排除绝区零）**：
   - **最高标杆**：《明日方舟：终末地》（清冷双半球天光、微蓝机能灰阶、真实物理 PBR 场景硬表面 + 极净通透赛璐璐 NPR 角色）。
   - **坚决排除**：《绝区零》式高饱和度、噪点粗糙、波普涂鸦滤镜（网图多靠后期 MOD 滤镜加持，原生极显油腻脏热）。
4. **资产生产工业化（确立 Surgery 混合管线）**：
   - 彻底禁绝“Agent 用代码硬手搓火柴盒白模”；
   - 彻底禁绝“直接裸用未治理的 AI 糙模”；
   - 确立**「Tripo3D 2.0 原生底模 (85% 宏观体量) + Blender Python 手术修补 (15% 切除假玻璃与 2D 贴纸，嵌入正交窗框与真实 3D 货架陈列)」**。
5. **严禁虚假量化自嗨（必须真机验图）**：
   - 历史教训：地面建模 Agent 曾硬编码 `PASS` 验收指标，结果真机渲染是一片发光的纯蓝塑料滑板。
   - **铁律**：模型自称 `PASS` 绝不能当成验收证据，一切以真机 2K 渲染 `.png` 人眼审查为准。

---

## 二、 当前工程现状与资产审计（Current Status）

- **代码仓库**：`github.com/TimeCraker/games.git`，主开发目录为 `asternova/`。
- **当前开发阶段**：**M1 渲染垂直切片**（与 M2 动作骨架并行推进中）。

### 1. 已完成并达标验收的资产
- ✅ **Tier 2 核心建筑：折角便利店（`convenience_store.glb`）**：
  - 通过 `surgery_convenience_store_body.py` 完成手术；
  - 剔除前脸破碎三角面与漂浮飞刃，嵌入正交深灰铝合金窗框与高透双层 PBR 玻璃；
  - 彻底清除室内 2D 贴纸，植入真实 3D 实体货架（Gondola Racks）、彩色商品盒、天花板暖白漫射 LED 与向外泼洒的迎宾地灯；
  - 真机双机位验收通过（commit `7768db0`）。
- ✅ **武器系统：专属佩刀「星霜月华」（`aster_katana.glb`）**：
  - 899 三角面（刀身 503 面，刀鞘 396 面），原点统一锁定在刀鞘口 `(0,0,0)` 实现零偏置出入鞘；
  - 单张 2K Atlas 图集，具备 3D Web 检视器与 Godot 视口。
- ✅ **渲染核心着色器升级**：
  - `toon_face.gdshader`：仰角解耦（`pitch_clamp = 0.15`）+ 正向平滑法线混合（0.70），彻底根除眼窝与鼻梁三角黑斑；
  - `toon_character.gdshader`：移除兼容模式降权 hack，集成 Kajiya-Kay 发丝各向异性天使环高光；
  - `endfield_studio_environment.tres`：Forward+、AgX 模式 4、全分辨率 SSAO、SSR、弱冷体积雾（密度 0.012，石板蓝雾色）。

### 2. 正在并行的外部 Agent 任务状态
- ✅ **环境与场景总装 Agent（已交付封板）**：
  - commit `a453424` 已落地：在 `render-lab/scenes/levels/m1_endfield_street.tscn` 纯实例化官方标准母版 `endfield_lighting_studio.tscn`，清除遮挡天空方块，完成 Tier 2 折角便利店、Tier 3 双联贩卖机、二次元法线球化樱花树与真实 PBR 沥青斑马线装配；
  - 产出三张 2K 评审图入库，经主脑与制作人评审达 75~80 分质量底线，正式作为 M1 场景基线封板；
  - 存在差距的 3 个短板（生活道具密度、墙体分缝与水渍贴花、角色动态）已记录在 `m1-render-vertical-slice.md` 与 `CONTENT_BACKLOG.md` 作为后期精修储备。
- ⏳ **战斗与角色驱动 Agent（进行中，主脑等待其完工）**：
  - 用户已派发工业级 Humanoid 任务书：正在为 Aster 执行 Blender 蒙皮手术（彻底切断两鞋粘连与长发贴腰权重污染），接入主脑已下载配置好的全套 Mixamo 动作库（`MeleeLib.res` 121 个近战动作 + `ShooterLib.res` 180 个身法动作 + `Mixamo_BoneMap.tres`）；
  - 主脑保持静默监控，等待该 Agent 交付标准带动画的模型与 `AnimationTree` 后，再进行 M2 战斗核心集成。

---

## 三、 核心技术标准与红线矩阵（Technical Redlines）

| 领域 | 核心标准与定案规范 | 严禁项（Redlines） |
| :--- | :--- | :--- |
| **渲染底座** | **Forward+ (Vulkan Clustered) + AgX 模式 4** | 严禁倒退为 `gl_compatibility`；严禁在 Shader 中硬写光照补偿 hack |
| **色彩与光影** | 终末地冷峻天光 + 45° 侧逆主阳光 + 盒投影反射探针 + SSAO + SSR | 严禁绝区零式重度饱和、暗部死黑与洋红浓雾 |
| **场景管线** | **AI 原生底模 (Tripo3D 2.0) + Blender 脚本几何手术 (Surgery) + 模块化嵌装** | 严禁代码手搓方块白模；严禁直接裸用有瑕疵的 AI 糙模；严禁窗内贴 2D 贴纸 |
| **角色面数** | **PC 旗舰档 60,000 ~ 85,000 三角面**（高精发型 15k~22k，服装 35k~45k） | 严禁使用 VRoid 粗糙素体；严禁单臂代码旋转假动作；严禁面部直接接收 PBR 漫反射 |
| **动作驱动** | **43 骨 Humanoid + BoneMap + AnimationTree (BlendSpace1D 0~7m/s)** | 严禁 Tween 强转单骨；严禁局部卡肉停滞全局 `Engine.time_scale` |
| **工程纪律** | 独立单元提交 Conventional Commits；测试截图在内存/临时目录销毁 | 严禁在 `art/` 散落中间调试碎图；严禁未见真机渲染图擅自判定 PASS |

---

## 四、 接手主脑的立即可行行动路线（Immediate Next Steps）

1. **监控并验收两大并行 Agent**：
   - ① **地面 Agent**：审查新生成的 `ground_pavement_review.png`，确保沥青有细腻微表面噪点质感、斑马线平直清晰、盲道倒角分明，且毫无自发光蓝光；
   - ② **角色 Agent**：审查 `aster_assembled.glb` 与 `AnimationTree`，验证 43 骨标准绑定、手肘膝盖自然弯曲、0~7m/s 呼吸待机与疾跑过渡。
2. **沙盒集成拼装（M1 垂直切片收官）**：
   - 在 `render-lab/` 中将已验收的 **折角便利店**、**修补后的地面道路**、**自动贩卖机**、**二次元法线球化樱花树** 与 **高精 Aster** 组装至标准 14:30 晴空场景；
   - 导出 低 / 中 / 高 三档画质真实 2K 渲染图，交付制作人 TimeCraker 终审。
3. **切入 M2 战斗骨架**：
   - 经制作人对 M1 画面拍板“过”后，将渲染资产与 Shader 同步至 `client-godot-v2`；
   - 跑通 GDScript 2.0 纯代码驱动的 3D ACT 核心（滑铲、蹬墙跳、四段流光拔刀、居合蓄力弹刀、4+1 构筑槽位）。
