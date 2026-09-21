<USER_REQUEST>
/goal 
【# 角色与任务定义
你是一名顶尖的二次元 3D 角色技术艺术家（Character Technical Artist），专精于虚幻/现代引擎级别的次世代二次元角色建模与 NPR（非真实感）渲染。
你的对标品质严格锁定为：**原神【至冬】（Snezhnaya / 愚人众执行官级高挑冷艳成熟建模，如「少女」哥伦比娅等）与《鸣潮》（Wuthering Waves）** 的 8.5 头身高精修长仙气美学，**坚决杜绝早期原神的“大头娃娃”幼态与 VRoid 的廉价玩具感**。

---

## 绝对红线禁令（违者直接打回重做）
1. ❌ **严禁使用 Python PIL 脚本写数学代码画贴图**：二次元眼睛与面部纹理是毫厘级的手绘艺术品，严禁用代码画椭圆或渐变色块充当眼睛与高光！贴图必须使用无损手绘高清贴图。
2. ❌ **严禁使用数学公式或坐标区间暴力拉伸顶点捏脸**：面部必须具备严格的五官环形布线（Edge Loops），严禁用 bmesh 遍历坐标硬拉下巴和眼眶。
3. ❌ **严禁使用低幼粗糙底模（如 VRoid 玩具素体）**：必须使用 8.5 头身成熟工业级美型基模。
4. ❌ **严禁虚假量化自嗨（Metric Gaming）**：严禁在报告中声称“相似度 93.8% 达到验收指标”并擅自结束！每一阶段必须由制作人（用户）肉眼确认 2K 纯净渲染图点头后，方可推进下一阶段。

---

## 技术规范与工业 SOP（必读）
- **完整制作管线指南**：`docs/pipeline/character-modeling-pipeline.md`
- **Aster 2D 官方立绘与三视图**：`art/characters/aster/turnaround-final.png`、`view_front.png`、`view_side.png`、`view_back.png`
- **本地工业级美型基模参考库**：`render-lab/models/`（重点参考 `columbina`【至冬执行官少女】与 `shenhe` 的成熟冷艳面部拓扑、天鹅颈与法线参考）
- **Blender 环境**：Blender 5.2.1 LTS（路径：`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`，已内置 Python 3.11 及 
<truncated 975 bytes>
与鼻翼脏阴影；
- **视差内凹星空眼**：凹面虹膜带来灵动的视线跟随，深邃水蓝渐变瞳孔配以独立自发光星芒高光，眼神清澈有神；
- **睫毛眉毛透发渲染通道**：预留 Stencil / Render Queue 透发可见通道。

---

## 交付与自查渲染要求
在 Blender 中设置柔和的三点布光与自然天光，渲染输出 **3 张 2K 分辨率无损 PNG 预览图** 保存至 `art/render_previews/milestone1/`：
1. `01_m1_body_silhouette_front.png`：正面全身照（检验 8.5 头身比、腿长与形体剪影）
2. `02_m1_face_three_quarter.png`：3/4 侧面面部特写（检验下颌线弧度与干净无脏斑的二次元阴影）
3. `03_m1_eyes_closeup.png`：双眼微距特写（检验星空眼神韵与高光质感）

产出后在对话中呈递图片路径，等待制作人人工审查。未获批准前不得进入 Milestone 2。】
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-05T12:33:31+08:00.

The user has mentioned some items in the form @[ITEM]. Here is extra information about the items that were mentioned by the user, in the order that they appear:

/goal is a [Slash Command]:
The user has marked this task with /goal, indicating that this task is intended to run for a long time without user input, e.g. overnight. You should be extra thorough and only stop when you are confident the goal has been completely fulfilled. The system will force you to continue execution, prompting you to audit your work until completion. Once complete, include <!-- GOAL_COMPLETE --> in your response. If the user explicitly asked to stop or cancel this goal, include <!-- GOAL_CANCELLED --> in your response to cancel the goal.
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Gemini 3.8 Flash (High). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>