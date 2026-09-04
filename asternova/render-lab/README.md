# Render Lab（渲染与建模试验场）

> **定位**：AsterNova M1 阶段专属设立的独立 3D 建模与 Godot 4.7 渲染切片沙盒（Sandbox）。与游戏网络代码、复杂 UI 彻底隔离，专注二次元 NPR 卡渲品质打磨。

---

## 目录结构

```text
asternova/render-lab/
├── project.godot              # Godot 4.7.2 独立工程根配置
├── models/                    # 3D 建模源工程与参考模型
│   └── aster/                 # Aster 角色模型
│       ├── aster_head_base_v2.blend   # 👑 当前最新工业级块面基模工程
│       └── textures/          # 贴图（干净瓷肌 aster_body_texture.png 等）
├── shaders/                   # 二次元卡渲着色器（Toon Shader）
│   ├── toon_character.gdshader        # 角色主着色器（Toon Ramp + 色偏映射）
│   ├── toon_hair.gdshader             # 头发着色器（各向异性天使光环）
│   ├── toon_face.gdshader             # 面部阴影着色器（SDF / 平滑半兰伯特）
│   └── outline.gdshader               # 背面扩张法描边着色器（Inverted Hull）
├── scenes/                    # 场景与舞台
│   ├── turnaround_stage.tscn  # 三视图同框验证专用舞台（前/后/侧/特写四机位）
│   └── street_sunset.tscn     # 黄昏樱花商店街切片场景
└── scripts/                   # 自动化批处理与截图脚本
    ├── turnaround_capture.gd  # Godot 自动化三视图捕获脚本
    ├── screenshot_capture.gd  # Godot 三档画质自动跑分与截图脚本
    └── *.py                   # Blender bpy 自动化拓扑/贴图批处理工具
```

---

## 常用开发命令（CLI 与 MCP 双模调用）

### 1. CLI 模式（后台自动化批处理）
```powershell
# 运行三视图比对舞台自动化截屏
godot --path "asternova/render-lab" "res://scenes/turnaround_stage.tscn"

# 运行黄昏商店街切片场景
godot --path "asternova/render-lab" "res://scenes/street_sunset.tscn"

# 使用本地 Blender 5.2.1 LTS 后台无头运行 Python 拓扑/贴图批处理脚本
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b "asternova/render-lab/models/aster/aster_head_base_v2.blend" -P "asternova/render-lab/scripts/your_script.py"
```

### 2. MCP 模式（前台可视化交互式协同）
- **Godot MCP**：通过 `@coding-solo/godot-mcp` 协议工具随时拉起编辑器、运行调试、动态审查场景节点或实时读取运行报错。
- **Blender MCP**：用户双击桌面快捷方式打开 Blender 界面后，按键盘 `N` 键打开右侧栏，在 **MCP for Blender** 面板点击 **Start MCP Server**，Agent 即可通过 MCP 协议对活动视口实时发送指令并所见即所得修改模型。


---

## 阶段验收与主客户端迁移

- **验收基准**：严格以 `asternova/art/characters/aster/turnaround-final.png` 为唯一 1:1 对比基准，要求面部、发型、发饰、领结全部就位后综合相似度 ≥ 90%。
- **迁移路径**：在 `render-lab` 验收通过后，模型 GLB 文件、KTX2 压缩贴图以及 Shader 文件将直接同步复制搬入 `asternova/client-godot/` 正式客户端工程。
