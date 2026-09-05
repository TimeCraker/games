# Render Lab（渲染与建模试验场）

> **定位**：AsterNova M1 阶段专属设立的独立 3D 建模与 Godot 4.7 渲染切片沙盒（Sandbox）。与游戏网络代码、复杂 UI 彻底隔离，专注二次元 NPR 卡渲品质打磨。

---

## 目录结构

```text
asternova/render-lab/
├── project.godot              # Godot 4.7.2 独立工程根配置
├── models/                    # 3D 建模源工程与参考模型
│   ├── aster/                 # Aster 角色模型（基模工程与贴图）
│   │   ├── aster_head_base_v2.blend   # 👑 当前最新工业级块面基模工程
│   │   └── textures/          # 贴图（干净瓷肌 aster_body_texture.png 等）
│   └── weapons/               # 武器与道具 3D 资产库
│       └── aster_katana/      # Aster 专属佩刀「星霜月华」全套资产
│           ├── aster_katana.blend         # 🗡️ Blender 5.2 建模源工程（双分件+描边）
│           ├── aster_katana.glb           # 📦 游戏标准 glTF 资产（899 面，116KB）
│           ├── aster_katana_3d_viewer.html # 🌐 自包含 3D Web 检视器（双击秒开）
│           ├── katana_preview.png         # 🖼️ 五视角高清合成验收看板
│           └── textures/                  # 2K NPR 贴图图集（tex_katana_basecolor.png）
├── shaders/                   # 二次元卡渲着色器（Toon Shader）
│   ├── toon_character.gdshader        # 角色主着色器（Toon Ramp + 色偏映射）
│   ├── toon_hair.gdshader             # 头发着色器（各向异性天使光环）
│   ├── toon_face.gdshader             # 面部阴影着色器（SDF / 平滑半兰伯特）
│   └── outline.gdshader               # 背面扩张法描边着色器（Inverted Hull）
├── scenes/                    # 场景与舞台
│   ├── turnaround_stage.tscn  # 三视图同框验证专用舞台（前/后/侧/特写四机位）
│   ├── weapon_viewer.tscn     # 🗡️ 武器 360° 实时交互检视舞台（支持拔刀/特写）
│   └── street_sunset.tscn     # 黄昏樱花商店街切片场景
└── scripts/                   # 自动化批处理与截图脚本
    ├── turnaround_capture.gd  # Godot 自动化三视图捕获脚本
    ├── screenshot_capture.gd  # Godot 三档画质自动跑分与截图脚本
    ├── weapon_viewer.gd       # 🗡️ 武器 360° Orbit 相机与 Tween 拔刀驱动脚本
    ├── build_aster_katana_mesh.py # 佩刀自动化建模与 GLB 导出
    ├── build_katana_texture.py    # 佩刀 2K NPR 贴图程序化绘制
    └── generate_katana_web_viewer.py # 佩刀 3D Web 检视器生成器
```

---

## 常用开发命令（CLI 与 MCP 双模调用）

### 1. CLI 模式（后台自动化批处理）
```powershell
# 运行武器 360° 实时交互检视窗口（支持鼠标拖拽、滚轮缩放、空格拔刀）
godot --path "asternova/render-lab" "res://scenes/weapon_viewer.tscn"

# 运行三视图比对舞台自动化截屏
godot --path "asternova/render-lab" "res://scenes/turnaround_stage.tscn"

# 运行黄昏商店街切片场景
godot --path "asternova/render-lab" "res://scenes/street_sunset.tscn"

# 使用本地 Blender 5.2.1 LTS 后台无头运行 Python 拓扑/贴图批处理脚本
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b "asternova/render-lab/models/weapons/aster_katana/aster_katana.blend" -P "asternova/render-lab/scripts/build_aster_katana_mesh.py"
```

### 2. MCP 模式（前台可视化交互式协同）
- **Godot MCP**：通过 `@coding-solo/godot-mcp` 协议工具随时拉起编辑器、运行调试、动态审查场景节点或实时读取运行报错。
- **Blender MCP**：用户双击桌面快捷方式打开 Blender 界面后，按键盘 `N` 键打开右侧栏，在 **MCP for Blender** 面板点击 **Start MCP Server**，Agent 即可通过 MCP 协议对活动视口实时发送指令并所见即所得修改模型。


---

## 阶段验收与主客户端迁移

- **验收基准**：严格以 `asternova/art/characters/aster/turnaround-final.png` 为唯一 1:1 对比基准，要求面部、发型、发饰、领结全部就位后综合相似度 ≥ 90%。
- **迁移路径**：在 `render-lab` 验收通过后，模型 GLB 文件、KTX2 压缩贴图以及 Shader 文件将直接同步复制搬入 `asternova/client-godot-v2/` 正式客户端工程。
