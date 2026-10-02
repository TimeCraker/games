# 白色角色静态样板

更新：2026-10-02。唯一制作源为 `white_rework_working.blend`。当前 5/6：静态候选已完成内部多角度检查，用户外观确认仍待完成。紫色、橙色和绑定尚未开始。

## 当前制作对象

- `Head_Work`：原眉眼、基础几何及 UV 保留；使用原贴图与柔和面部材质。`Head_ScalpClosure` 补头顶/后脑内层。
- `Hair_Sections_Work`：保留原主要发束与长发设计。`ScalpLandmarks_Cage` 控制头型适配；`FringeThickness_Control` 只减薄前额外层；`SideLengths_BehindShoulder_Cage` 将肩旁长发移至袖子后。重复耳周和小碎件用可恢复 MASK 隐藏。耳周原烘焙杂色使用独立银白材质。
- `Outfit_Trimmed_Work`：从原服装派生，保留腰带、图形衣摆、手套及独立扣件。旧袖子与前臂衣片通过原生 Bisect 裁切。白色前襟重新分配布料材质，补衣料厚度；长衣摆使用单独长度笼调整。
- `Sleeve_Anatomical_Work_-1/1`：重建四边形袖筒，用原生 Cloth 与身体碰撞得到褶皱，再冻结为可编辑四边形网格。生产导出不依赖临时模拟缓存。模拟前来源保存在隐藏归档。
- `SleeveUpperBinding_*`、`ShoulderWebbing_*`、`SleeveCuff_Fitted_*`：连接袖子、肩部与前臂；前臂连续表面恢复。
- `SleeveRibbon_Outer/Inset_*`：接在袖带后侧的蓝黑垂带，避免穿过手臂。

`EXPORT_White` 当前包含 23 个可见网格。原资产、旧装配和被撤下的造型试验在隐藏来源/归档集合中保留。

## 验证与边界

三件原始 GLB 哈希未变，头部基础几何和 UV 哈希与原归档一致。制作源、导出与渲染报告哈希一致。新版没有蒙皮与动作；白色外观确认后再继续紫橙和绑定。

当前是供用户验收的静态样板。海报的姿势、透视、光照及二维发束表现与正交休止模型不同；不报告相似度，不把导出成功当成用户确认。未测帧时，也未制作最终面部表情或动态布料。

## 最新证据

- `review/assembly_fit_comparison_20261002.png`：海报、上轮保存版、当前全身同框。
- `review/assembly_head_comparison_20261002.png`：原眉眼保留与头部正侧面前后对照。
- `review/assembly_fit_20261002/`：全身/头部/中性材质固定视图，来源及结构报告。
- `review/godot_20261002/`：当前实际引擎多视图和报告。

`source_detail_*`、旧 `godot/`、`checkpoint_*` 和 `hair_fit_*` 为历史检查点。

## 编辑与查看

直接编辑 working blend；导出器只读取 `EXPORT_White`，不从旧装配参数重建。不要运行旧脚本覆盖它。

从 games 根目录双击 `启动白色静态样板.bat`：1 当前、2 旧休止、3 旧 Idle；V 正侧背、H 头部、M 中性材质、P 转台、N Toon/PBR；右键环绕、滚轮缩放。

导出与固定视图入口：`scripts/pipeline/characters/export_static_review.py`、`render_static_review.py`。恢复入口和完整命令见 `docs/stage-specs/character-art-rework-handoff.md`。
