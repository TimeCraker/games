# AsterNova 跨设备接力全量技术交接与后续规划简报（Session Continuation Handover）

> **生效基准 Commit**：`fe6d5c4`（已推送到 GitHub origin/main）  
> **文档目的**：供开发者换电脑后，新设备上的 Agent **1 秒内完整继承本会话的所有核心决策、技术演进教训、已修复冲突与后续明确推进计划**，彻底避免重复试错或路线偏离。

---

## 一、 项目背景与当前技术栈基线

* **项目名称**：AsterNova（单机为主的 3D 动作 Roguelite，对标《绝区零》《鸣潮》自由视角高速战斗，兼具 2~6 人房主联机）。
* **引擎架构**：
  * **主客户端**：`asternova/client-godot-v2/`（基于 **Godot 4.7.2**，Forward+ 渲染与全端统一 Compatibility 兼容）。
  * **模拟核心**：60Hz 固定步长 GDScript 纯代码驱动身法与战斗状态机，单机本地直调，联机房主独裁。
  * **联机机制**：Steam 版走 Valve 免费中继网络（零自建服务器），原 Go 中心服务端全面一期封存（FROZEN）。
* **美术基准与唯一真理源**：
  * 女主角 Aster 定稿三视图：[`asternova/art/characters/aster/turnaround-final.png`](../../art/characters/aster/turnaround-final.png)（A-pose，珍珠白长发，白色常服系，165cm，8.0~8.5 头身仙气体态）。
  * 场景设计哲学：全面对标**《明日方舟：终末地》（Arknights: Endfield）**工业机能美学（低面数、大倒角、挑檐外挂走廊、丰富小道具、冷暖对冲雨夜光影）。

---

## 二、 核心认知红线与重大战略转折（新 Agent 绝对禁令）

在历史迭代中踩过严重技术陷阱，**新接手的 Agent 必须绝对恪守以下五条铁律**：

1. ❌ **严禁 Agent 用几何代码手搓场景建筑白模**：
   * 靠代码拼 Cube/Cylinder 的火柴盒房屋毫无结构进深与工业剪影，千禧年 PS2 积木水平，再强的光影也无法弥补拙劣几何。
2. ❌ **严禁试图用 AI 3D 一键生成整张开放大地图**：
   * 现阶段 3D AI（如 Tripo3D）仅擅长“单体物体（Props/Single Buildings）”，整街生成会塌陷成无法行走、无法穿透的实心畸形泥团。
3. ❌ **严禁使用 VRoid 玩具素体或第三方 MMD 模型缝合拆件**：
   * 早期缝合（VRoid、原神/鸣潮 MMD 拆件）导致面部恐怖谷、布线炸裂且存在侵权隐患。现已彻底清空仓库内 130MB+ 第三方 MMD 模型（`ayaka`, `columbina` 等）及 28 个排查脚本，**全面确立 100% 原生 AI 生产路线**。
4. ❌ **严禁使用 Python PIL 等数学代码绘制角色五官/眼球贴图**：
   * 用代码算圆画坐标是“死鱼眼”的直接元凶。二次元角色面部、五官、眼睛必须使用手绘/烘焙或 AI 原生图集（硬表面刀剑道具除外）。
5. ❌ **严禁虚假量化自嗨（Metric Gaming）**：
   * 严禁在脚本中打印“相似度 95%”等伪指标宣布完成，每一阶段交付必须由**制作人肉眼审查真实 2K 渲染图**作为唯一验收标准。

---

## 三、 本次会话完成的关键工作（已固化并入库）

### 1. 物理目录与废弃资产大整肃（释放 150MB+ 空间）
* 清除了根目录下误生成的 `art/`, `client-godot-v2/`, `render-lab/` 3 个未跟踪冗余副本；
* 清理了 `asternova/` 根目录遗留的 4 张散落测试贴图；
* 清除了磁盘上所有 Blender 自动备份缓存（`*.blend1`）；
* 彻底删除了早期报废的 VRoid 模型（`victoria.vrm`, `aster_base.vrm`）以及用于拆件测试的 8 套第三方 MMD 目录与 28 个临时测试脚本。

### 2. 全套技术文档冲突与分歧修复（消除 7 处文档矛盾）
* **头身比终限定案**：统一以三视图为准，全网修正为 **165cm · 8.0~8.5 头身**（彻底清除 `STYLE.md` 旧版残留的 154cm/6.5 头身）；
* **发型面数分级规范**：主角 High 档预算为 **8,000~12,000 面**（保证长发分层立体与物理骨骼），中低档与 LOD1 严控在 **3,000~5,000 面**；
* **角色管线升级**：`architecture.md` 全面更新为「2D 定稿三视图 ➔ Tripo3D 2.0 原生生成 ➔ Blender Quad 重拓扑 ➔ Godot 4.7 组装」；
* **贴图哲学边界澄清**：明确有机角色面部禁代码绘制，硬表面冷兵器道具允许参数化图集流水线；
* **场景工业化四级分级体系（Tier 1~4）正式定案**：
  * **Tier 1 地面基础设施**：沥青路面、路沿石、盲道砖，严格走 **CS2 级 Trim Sheet / 平铺 PBR**（保证无缝大面积拼接、无接缝走样、极低显存）；
  * **Tier 2 核心单体建筑**：折角便利店、斜屋檐商铺，走 **GPT 原画 ➔ Tripo3D 生成外观 ➔ Blender 标定 2m/4m 网格并 Quad 减面**；
  * **Tier 3 街景高频小道具**：自动贩卖机、空调外机、垃圾桶、雨棚，走 **Tripo3D 独立原生 GLB ➔ 独立 Prefab 在引擎自由摆放**；
  * **Tier 4 远景天际线**：低模剪影体块 + 体积雾弱化；
* **过期文档修正**：`backend/docs/roadmap.md` 增加一期封存（FROZEN）标识；`render-lab/README.md` 迁移目标修正为 `client-godot-v2`；根 `README.md` 引擎版本统一修正为 `Godot 4.7.2`。

---

## 四、 换机后的下一步具体行动计划（Next Steps）

新电脑接手后，直接按以下两条主线有序推进：

### 路线 A：女主角 Aster 100% 原创二次元高模推进（当前就绪）
1. **输入就绪**：制作人从 Tripo3D 导出 Aster 高模（GLB 格式），拖入目录：  
   `asternova/art/models/raw_ai_sculpt/aster_raw_sculpt.glb`
2. **执行自动化摄入流水线**：
   ```powershell
   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P asternova/scripts/pipeline/process_phase1_sculpt.py
   ```
   * 该脚本已由 Agent 编写并验证完毕，会自动完成：对齐 1.650m 人体工学身高、双脚对齐 Z=0、应用摄影棚专业布光、并自动渲染 3 视角 2K 粘土线框图（`01_m1_front_silhouette_wire.png` 等）。
3. **Milestone 1 卡点验收**：制作人肉眼审查 2K 渲染线框图确认布线与形体。
4. **Milestone 2 材质与装配**：解耦极净面部 Shader（消除眼窝/鼻翼脏阴影）、2.5mm 内凹视差星空眼、泡泡袖与百褶裙物理骨骼（SpringBone）装配。

### 路线 B：场景终末地级机能美学升级（模块化替换）
1. **生图准备**：使用 GPT 生成 1 款折角便利店与 1 款日式双联自动贩卖机概念图（提示词模板见 `modular_art_and_asset_production_sop.md`）；
2. **单体生成**：放入 Tripo3D 导出独立 GLB；
3. **引擎实装**：放入工程进行 2m/4m 网格尺寸标定，挂载 `CollisionShape3D`，替换沙盒现有的火柴盒白模，并挂载 Godot 4.7 体积雾与湿地面反射，跑出神级雨夜质感！

---

## 五、 新电脑接力唤醒指令（直接复制发送）

在新电脑拉取代码（`git pull origin main`）后，打开 Antigravity 新建会话，**直接复制以下内容发送**：

```markdown
我换了电脑继续 AsterNova 项目开发，当前已拉取最新代码。
请首先阅读交接专档：
asternova/docs/pipeline/SESSION_CONTINUATION_HANDOVER.md
以及核心规范：
1. asternova/docs/pipeline/modular_art_and_asset_production_sop.md（AI 3D 原生单体生成 + Tier 1~4 场景分级体系）
2. asternova/docs/STYLE.md（Aster 165cm · 8.0~8.5 头身，发型 High 档 8k-12k / LOD 档 3k-5k）

我准备推进 Aster 模型摄入或场景道具更新，请汇报你已完全掌握上述上下文并处于就绪状态。
```
