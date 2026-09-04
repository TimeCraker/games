# Aster 专属武器专档：佩刀「星霜月华」（Seisou Gekka）

> **状态**：✅ 3D 低模制作、贴图绘制与可拔刀分件装配已定稿验收（2026-09-04）  
> **视觉基准**：[`weapon-turnaround-final.png`](weapon-turnaround-final.png)（本目录）  
> **角色归属**：[Aster 角色专档](aster.md)  
> **工业化复刻 SOP**：[docs/pipeline/weapon-modeling-pipeline.md](../../../docs/pipeline/weapon-modeling-pipeline.md)

---

## 1. 武器设定与美学特征

| 设定维度 | 规范数值与特征 |
| :--- | :--- |
| **武器全称** | **星霜月华**（日文暂定：星霜月華 / せいそうげっか，英文：Seisou Gekka） |
| **武器类型** | 风格化二次元微弧太刀（Dual-Mesh 可拔刀双分件装配） |
| **核心尺寸** | 全长约 **95.9cm**（刀刃 70.0cm，刀柄 24.5cm，刀鞘 72.1cm） |
| **装配原点** | 统一锁定在【刀鞘口（Koiguchi）正中心】`(0, 0, 0)`，出入鞘零偏置 |
| **持刀方式** | 平常常态【挂载于 Aster 左腰封】，拔刀战斗时【右手握持刀柄，出鞘挥砍】 |
| **美学配色** | 象牙白 65% · 浅天蓝 15% · 深蓝 10% · 香槟微金 8% · 水蓝宝石 2% |

### 核心分件设计：
1. **刀身组（`Blade_Mesh` · 503 三角面）**：
   - **刀刃（Blade）**：微弧镐造（Shinogi-zukuri）截面，冷天蓝渐变钢材与波浪形烧刃纹（Hamon），切先（Kissaki）利落分明；
   - **刀镡护手（Tsuba）**：4 瓣香槟金流线立体造型，内嵌象牙白花瓣，中心镶嵌水蓝星钻；
   - **刀柄（Tsuka）**：深蓝菱形目贯柄卷编织纹（`#18243B` 至 `#223E75`）；
   - **柄尾吊坠（Kashira Tassel）**：柄尾金色封盖，垂挂双缕浅蓝细丝带与金色四芒星水蓝宝石吊坠。
2. **刀鞘组（`Scabbard_Mesh` · 396 三角面）**：
   - **鞘身（Saya）**：象牙白微珠光扁椭圆鞘身（`#E0E0E8`，防爆光），外饰金色四芒星阵列刻纹；
   - **鞘口包金（Koiguchi）**：香槟金封口环，开有与刀身严丝合缝的插槽；
   - **系绪蝴蝶结（Sageo）**：鞘口下方立体浅蓝优雅蝴蝶结与下垂双带，尾部金色金属封头；
   - **鞘尾（Kojiri）**：香槟金包角与水蓝宝石。

---

## 2. 资产与代码分布全景地图（在哪里找？）

本项目关于该武器的资产、脚本与代码分别位于以下位置：

```text
asternova/
├── art/characters/aster/
│   ├── weapon-turnaround-final.png       # 🎨 官方 2D 正交全分件设定图（美术源头）
│   └── weapon.md                         # 📝 本文档（武器美术资产专档）
│
├── render-lab/models/weapons/aster_katana/
│   ├── aster_katana.blend                # 🛠️ Blender 5.2 建模源工程（双分件+描边）
│   ├── aster_katana.glb                  # 📦 游戏通用 glTF 2.0 资产（899 面，116KB）
│   ├── textures/tex_katana_basecolor.png # 🎨 2048x2048 NPR 贴图图集
│   ├── katana_preview.png                # 🖼️ 官方五视角高清合成验收看板
│   └── aster_katana_3d_viewer.html       # 🌐 自包含 3D Web 检视器（双击浏览器秒开）
│
├── render-lab/scripts/                    # ⚙️ 自动化构建与生成脚本
│   ├── build_aster_katana_mesh.py        # Blender 自动化拓扑与导出脚本
│   ├── build_katana_texture.py           # 2K NPR 贴图程序化绘制脚本
│   ├── composite_katana_showcase.py      # 自动化多视角出图与合成看板脚本
│   └── generate_katana_web_viewer.py     # 3D Web 检视器生成脚本
│
├── render-lab/scenes/                     # 🎮 引擎内独立检视视口
│   ├── weapon_viewer.tscn                # Godot 4.7 独立展示台场景
│   └── ../scripts/weapon_viewer.gd       # 交互代码（360°旋转/缩放/空格拔刀动画）
│
└── client-godot-v2/                       # ⚔️ 正式游戏客户端（下一步挂载装配）
    └── 角色右手插槽挂载（Hand_R_Weapon_Socket）与腰部插槽（Pelvis_L_Scabbard_Socket）
```

---

## 3. 怎样进行 360° 交互检视？

1. **方式 1：双击 Web 3D 检视器（最轻量推荐）**：
   - 文件：[`render-lab/models/weapons/aster_katana/aster_katana_3d_viewer.html`](../../../render-lab/models/weapons/aster_katana/aster_katana_3d_viewer.html)
   - 效果：在 Edge / Chrome 浏览器中秒开，支持鼠标 360° 拖拽旋转、滚轮变焦、按空格键拔刀/收刀、按 `W` 切换线框拓扑、按 `1~5` 特写对焦。
2. **方式 2：Godot 引擎原生场景**：
   - 场景文件：[`render-lab/scenes/weapon_viewer.tscn`](../../../render-lab/scenes/weapon_viewer.tscn)
3. **方式 3：Blender 5.2 视口**：
   - 源工程：[`render-lab/models/weapons/aster_katana/aster_katana.blend`](../../../render-lab/models/weapons/aster_katana/aster_katana.blend)

---

## 4. 后续新武器复刻指引

如需制作新的角色专属武器或通用武器，请直接查阅通用工业化实践路线文档：  
👉 [**`docs/pipeline/weapon-modeling-pipeline.md`**](../../../docs/pipeline/weapon-modeling-pipeline.md)
