# 白色角色：原资产细节装配候选，未通过最终美术验收

更新：2026-10-01 晚。唯一制作源仍为 `white_rework_working.blend`，纹理已打包。宏观进度 3/6；白色尚未确认，未制作紫橙、未绑定。

## 当前对象

- `Head_Work`：保留原五官、几何和 UV。新增独立 `Head_ScalpClosure` 补头顶与后脑内层。
- `Hair_ScalpFit_Work`：保留原长发造型及 UV，继承修改器求值结果已冻结为网格，当前只有一个贴合笼。`Edit_Crown/Bangs/SideLocks/BackLocks` 用于后续分区编辑。
- `Outfit_SourceDetail_Work`：从原服装派生，恢复褶皱、腰带、衣摆图形与手套，独立校准领口和袖子。袖子选择限定连通衣物部件；腰腿饰件不随袖子变形。
- `SleeveCuff_Fitted_-1/1`：贴合前臂的袖口；身体的袖内遮罩可关闭恢复。
- `EXPORT_White` 当前导出 13 个可见网格。旧硬片服装和旧头发保留隐藏；不要重新启用旧试验。

## 已验证与剩余问题

原始三件 GLB 哈希未变；头部几何和 UV 与原归档相同；源文件、导出记录和渲染记录哈希一致。Godot 4.7.2 Forward+ 实际载入并完成 10 张截图，进程退出码 0。新版 0 蒙皮、0 动作。

服装轮廓与原设计的层次明显恢复。头部贴合改进有限；源肩饰破碎感、耳周细节、脸部烘焙阴影及局部接缝仍需打磨。未测性能，未完成最终 NPR，未获得用户美术确认。

## 最新证据

- `review/source_detail_comparison.png`：海报、接手时、当前全身对照。模型前后同相机、同灯光。
- `review/source_detail_head_comparison.png`：头部前后正侧面对照。
- `review/source_detail_assembly/`：当前正/左右侧/背、三分之四、头部和中性材质，以及来源验证报告。
- `review/godot/`：当前实际引擎截图和报告。
- 旧 `checkpoint_*`、`hair_fit_*`、`poster_old_current.png` 是历史检查点。

## 继续编辑与查看

直接编辑 working blend。`white_static_master.blend` 为被否定的历史试验。不要运行旧装配参数脚本覆盖当前源。

从 games 根目录双击 `启动白色静态样板.bat`：1 当前、2 旧休止、3 旧 Idle；V 正侧背、H 头部、M 中性材质、P 转台、N Toon/PBR；右键环绕、滚轮缩放。

导出器 `scripts/pipeline/characters/export_static_review.py` 读取工作源；新增 `render_static_review.py` 读取工作源并以固定相机出图。两者都不保存或重建源文件。

当前执行入口与后续问题详见 `docs/stage-specs/character-art-rework-handoff.md`。
