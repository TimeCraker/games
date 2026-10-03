# 紫色角色返工工程

2026-10-03 最新状态：**用户已否定本轮简化服装替代方案，并要求本 Agent 停止制作、交接其他 Agent。** 原始三件 GLB、旧 `purple_master.blend` 与旧运行 `purple.glb` 均保留。完整原计划、失败原因、资产位置及恢复线索见 [紫色交接文档](../../../../docs/stage-specs/purple-character-rework-handoff.md)。

`purple_rework_working.blend` 保存了被否定的工作结果，仅作为失败证据和恢复调查，**不能直接作为后续绑定基础**。原始网格在隐藏的 `SOURCE_Purple_Immutable`；工作部件在 `WORK_Purple`；发束与服装适配笼在 `EDIT_Purple_Fit_Cages`；被替换的兜帽结构另行归档。源眉眼和身体保留，原兜帽与袖口垂饰采用可恢复遮罩，源 GLB 不删改。

历史改动：独立兜帽外层与紫色内衬、帽沿和星饰；主长发分区适配；袖子内衬、后背布片与腰带；袖口垂饰分件及连接链。原生 MCP 接通后又将大块胸腰与衣摆遮罩，改用环形束腰、简单短裙、侧折片及长条分层衣摆等替代。虽然保留了原脸与部分钟袖/袖口，这些替代件丢失了原服装的设计细节与海报层次，已被用户否定，不能继续作为成品方向。

Blender MCP 已通过独立 stdio 客户端验证修改与截图恢复链路。2026-10-03 重启 Codex 后，本聊天的原生 `blender_purple` 工具已加载；实际调用确认活动文件为本目录静态制作源、端口为 9877，并成功取得视口截图。插件协议 9 低于服务端预期的 13，当前场景读取、代码执行与截图调用已实测成功。证据见 [原生 MCP 视口](review/mcp/native_client/active_front.png)、[原生连接记录](review/mcp/native_client/connection_report.json) 和 [此前修改恢复记录](review/mcp/edit_probe/connection_report.json)。

`purple_rework.py` 只读取已保存工程进行固定视图渲染和静态 GLB 导出，并检查源文件哈希不变。它不按旧装配参数重新生成网格。

本轮 [海报与失败方案前后对照](review/mcp/garment_rebuild/comparison.png)、正/左/右/背及头部特写均来自原生 MCP 活动场景截图；原始 GLB 哈希保持不变，记录见 [历史修复报告](review/mcp/garment_rebuild/repair_report.json)。这些图片保留为反例，不是验收件。

本目录其余绑定、动作和 Godot 文件是较早开发检查产物，未对应当前工作结果，旧检查图不能证明当前模型通过验收。本 Agent 已停止制作；接手者需按原始美术资产重新判断修复方案，详见 [紫色 Stage Spec](../../../../docs/stage-specs/purple-character-rework.md) 和交接文档。当前没有执行资产回退或删除。
