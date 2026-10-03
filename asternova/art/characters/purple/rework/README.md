# 紫色角色返工工程

2026-10-03：静态制作候选，尚未通过用户美术验收。原始三件 GLB、旧 `purple_master.blend` 与旧运行 `purple.glb` 均保留。

`purple_rework_working.blend` 是当前静态制作源。原始网格在隐藏的 `SOURCE_Purple_Immutable`；工作部件在 `WORK_Purple`；发束与服装适配笼在 `EDIT_Purple_Fit_Cages`；被替换的兜帽结构另行归档。源眉眼和身体保留，原兜帽与袖口垂饰采用可恢复遮罩，源 GLB 不删改。

已制作：独立兜帽外层与紫色内衬、帽沿和星饰；主长发分区适配；袖子内衬、后背布片与腰带；袖口垂饰分件及连接链。衣服仍有源网格碎片和接缝问题，兜帽细节、脸部气质和海报层次仍待美术复核。

Blender MCP 已通过独立 stdio 客户端验证修改与截图恢复链路。2026-10-03 重启 Codex 后，本聊天的原生 `blender_purple` 工具已加载；实际调用确认活动文件为本目录静态制作源、端口为 9877，并成功取得视口截图。插件协议 9 低于服务端预期的 13，当前场景读取、代码执行与截图调用已实测成功。证据见 [原生 MCP 视口](review/mcp/native_client/active_front.png)、[原生连接记录](review/mcp/native_client/connection_report.json) 和 [此前修改恢复记录](review/mcp/edit_probe/connection_report.json)。

`purple_rework.py` 只读取已保存工程进行固定视图渲染和静态 GLB 导出，并检查源文件哈希不变。它不按旧装配参数重新生成网格。

本目录其余绑定、动作和 Godot 文件仍是开发中的检查产物。最新静态结构尚未同步到运行导出，旧检查图不能证明当前模型通过验收。下一步通过活动 MCP 继续检查静态轮廓和接缝，再同步绑定工程及运行资源；完整进度见 [紫色 Stage Spec](../../../../docs/stage-specs/purple-character-rework.md)。
