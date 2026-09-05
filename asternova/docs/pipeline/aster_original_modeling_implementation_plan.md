# Aster 100% 原创二次元高模工业化制作方案（Implementation Plan）

依据 `/grill-me` 深度研讨定论，女主角 Aster 的 3D 原创模型彻底告别“侵权拆件缝合”与“纯代码几何硬凑”两条死胡同，正式确立**「AI 3D 原生多视角神经网格重建 + Blender 工业级 Quad 重拓扑 + 三阶段制作人卡点验收」**的工业化标准管线。

---

## 一、 核心技术架构定案（Decisions Finalized）

| 模块 / 环节 | 终审定案技术路径 | 核心技术标准与实现细节 |
| :--- | :--- | :--- |
| **原始几何网格获取** | **AI 3D 原生多视角曲面重建** | 以终版 2D 三视图（`art/characters/aster/turnaround-final.png`）为输入源，由用户通过网页端（Tripo3D 2.0 / Deemos Rodin Gen-2）1 分钟极速生成原生连续高精雕刻网格（.glb / .obj），保留波浪发、泡泡袖与褶皱。 |
| **网格规整与拓扑** | **Blender 四边面重拓扑 (Quad Remesh)** | Agent 将原始 10~20 万面高模重拓扑为 **3.5 万~ 4.5 万三角面**的标准游戏四边面低模；面部环形拓扑对齐、开挖裙底与身体保持物理隔离。 |
| **面部与眼神工艺** | **解耦 NPR 干净面部 + 视差凹面星空眼** | 面部解耦独立材质，采用 SDF 阈值平滑阴影（绝不产生眼窝/鼻下脏阴影）；虹膜与瞳孔向内物理微凹 2~3mm 产生视差注视效果；星空眼与星芒高光独立自发光。 |
| **骨骼与物理动态** | **标准 Humanoid 骨架 + 次级 SpringBone** | 躯干四肢对齐标准 Humanoid 人形骨骼（与 Mixamo 及 Godot 通用动作库 100% 兼容）；长发发簇、双层百褶裙、背后缎带挂载次级弹簧骨，高速滑铲与冲刺动态飘逸。 |
| **验收管控机制** | **三阶段制作人视觉卡点制** | 严禁 Agent 虚假量化自嗨。每个阶段必须输出指定视角的 2K 纯净实机渲染图，由制作人亲自在对话中确认后方可推进。 |

---

## 二、 阶段化实施计划（Phased Milestones）

### 阶段 0：三视图 3D 原始雕刻网格输入（前置输入）
- **操作方**：制作人用户（极速 1 分钟操作）。
- **执行流程**：
  1. 打开本地已有的高精三视图：`art/characters/aster/turnaround-final.png`；
  2. 访问 Tripo3D（https://www.tripo3d.ai）或 Deemos Rodin（https://hyperhuman.deemos.com/rodin）；
  3. 上传该三视图，生成并导出高精 `.glb` 格式；
  4. 放入工程目录：`asternova/art/models/raw_ai_sculpt/aster_raw_sculpt.glb`。

---

### 阶段 1：几何重拓扑、分层分件与 A-Pose 标定（Milestone 1 - Mesh Topology）
- **操作方**：Agent 自动化执行。
- **任务目标**：
  1. 导入 `aster_raw_sculpt.glb`，在 Blender 中对齐 8.5 头身鸣潮级体态与 A-Pose（双臂下垂 38°）；
  2. 拆解分层部件：
     - `Head_Mesh`（面部与头部基座）
     - `Hair_Mesh`（前刘海、鬓角侧发、后腰长发，进行法线球化）
     - `Body_Skin_Mesh`（锁骨、天鹅颈、手臂、修长双腿）
     - `Costume_Mesh`（立领衬衫、维多利亚泡泡袖、高腰封、双层百褶裙）
     - `Acc_Shoes_Mesh`（胸前缎带胸针、玛丽珍皮鞋与蕾丝短袜）
  3. 执行 Quad Remeshing，输出三角面控制在 35,000 ~ 45,000 范围的标准四边面资产。
- **阶段 1 验收交付物**：
  - `art/models/aster_m1_topology.blend` / `.glb`
  - 交付 2K 灰模线框多视角图（检验布线曲率与轮廓还原度）：
    - `01_m1_front_silhouette_wire.png`
    - `02_m1_three_quarter_clay.png`
    - `03_m1_back_hair_flow.png`
- **卡点规则**：由制作人审核线框与体态无误后进入阶段 2。

---

### 阶段 2：NPR 极净面部、星空眼与高精材质装配（Milestone 2 - Shading & Materials）
- **操作方**：Agent 自动化执行。
- **任务目标**：
  1. 制作内凹 2.5mm 视差星空眼网格，配置冰蓝渐变底色与自发光四角星芒；
  2. 挂载 SDF 面部光照着色器，配置冷白肤色无脏斑卡渲；
  3. 对齐原画色彩图集（Color Atlas），为百褶裙配置半透明双通道深度内衬，为泡泡袖与领结配置高光反射；
  4. 配置 Solidify Inverted Hull 反转法线轮廓描边。
- **阶段 2 验收交付物**：
  - `art/models/aster_m2_materials.blend` / `.glb`
  - 交付 2K 高清全彩 NPR 渲染图：
    - `01_m2_face_macro_closeup.png`（面部与星空眼微距特写）
    - `02_m2_full_costume_front.png`（全身正视图，检验色彩与服饰层次）
    - `03_m2_skirt_veil_transparency.png`（裙摆与泡泡袖轻纱质感特写）
- **卡点规则**：由制作人审查神态、五官、色彩是否 1:1 还原原画。

---

### 阶段 3：标准 Humanoid 骨骼绑定与 Godot 4.7 引擎实装（Milestone 3 - Rigging & Engine Integration）
- **操作方**：Agent 自动化执行。
- **任务目标**：
  1. 绑定行业通用 Humanoid 标准骨架，确保与现有的 `player_controller.gd` 和测试动画无缝对接；
  2. 为后部长发束、百褶裙摆、后腰飘带装配次级物理骨骼链；
  3. 组装 Godot 4.7 正式角色场景：`client-godot-v2/scenes/entities/player/aster_player.tscn`；
  4. 挂载武器插槽（右手刀鞘与拔刀握持点）；
  5. 运行实机 60 帧无头自动化验证，检验奔跑、急停滑铲、空中下砸及拔刀攻击状态下物理摆动无拉丝、无穿模。
- **阶段 3 验收交付物**：
  - `client-godot-v2/scenes/entities/player/aster_player.tscn`
  - 实机动作渲染看板与运行日志。

---

## 三、 验证与验收标准（Verification Plan）

1. **绝对合规红线**：全工程零 miHoYo / PMX / 商业闭源盗用网格，100% 具备自主知识产权与商业化发行资质。
2. **美学神韵红线**：
   - 彻底告别圆柱硬凑与纸扎纸人；
   - 8.5 头身鸣潮级仙气体态；
   - 泡泡袖、百褶裙与后部长发与 `turnaround-final.png` 剪影重合度 ≥ 90%。
3. **引擎运行标准**：
   - 面数严控在 4.5 万三角面以内；
   - Draw Call ≤ 4；
   - Godot 4.7 Forward+ 渲染器下 120 FPS 丝滑运行。
