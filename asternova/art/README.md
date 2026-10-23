# AsterNova 美术资产库（Art Assets）

> **定位**：原画、源模型、参考图与渲染预览。游戏实际加载的资产在 `client-godot-v2/` 内，这里放的是它们的来源和参考。制作流程见 [docs/asset-pipeline.md](../docs/asset-pipeline.md)。

---

## 目录结构

```text
asternova/art/
├── README.md
├── characters/
│   ├── aster/          # Aster 设定：aster.md 人设档案、turnaround-final.png 定稿三视图、view_* 单视图、
│   │                   #             weapon-turnaround-final.png 佩刀「星霜月华」设定
│   └── source/         # 白/橙/紫三角色原始设定图与 AI 分件模型（只作参考，见下文）
├── models/
│   ├── source/         # Tripo 原始导出（只读，见下文）
│   ├── weapons/        # 佩刀 aster_katana 全套（游戏内用的是复制到 client-godot-v2/models/weapons/ 的 katana.glb）
│   ├── neighborhood/   # M1 街区源模型（街区、便利店、自动售货机），游戏里用的是 client-godot-v2 的副本
│   └── lumina_plaza/   # 旧光映广场源模型（游戏内已删除，留作素材）
├── references/         # 参考图（map_style/ 场景风格参考、便利店/售货机/地面/免费道具参考）
├── textures/           # .blend 源文件外链的贴图（改名或移动会让 .blend 丢贴图）
│   ├── nextgen_pbr/    #   M1 街区 modern_japan_neighborhood.blend 用
│   └── lumina_plaza/   #   光映广场 lumina_plaza_masterpiece.blend 用
├── ui/                 # 游戏界面资产
└── render_previews/    # 引擎实拍预览
    └── lighting/       # 四套光照预设实拍（docs/lighting-guide.md）
```

---

## 原始资产来源（只读，不要直接修改）

这些都是**参考资料**，不是可直接进游戏的角色：GLB 是 Tripo 生成的静态网格，没有骨骼和权重。要改就复制出去再改。

### Aster Tripo 原模：`models/source/aster_tripo_39caf44b/`

- Tripo 任务 ID：GLB `39caf44b-3bc4-41b8-976d-c0e921f0f2d5`，FBX `0215b75a-e182-49b2-b4fc-50205887eeab`
- 文件：`aster_source.glb`、`aster_source.fbx`、`textures/`（Tripo 贴图）

### 白/橙/紫三角色：`characters/source/<white|orange|purple>/`

2026-10-23 从本机 `C:\Users\TimeCraker\Pictures\游戏人物建模参考\<白色|橙色|紫色>\` 复制入库，内容未改；原目录里的 `归档_旧版备选`、`备选参考_*` 过程稿没有复制。三个 GLB 是 Tripo 分件生成，部件之间尺度不对应。

| 本目录 | 原文件 |
| :--- | :--- |
| `<角色>/poster/poster_main.*` | `海报参考图/01_*`（主选海报） |
| `white/poster/poster_alt_heels.jpg` | `白色/海报参考图/02_备选参考图_细高跟版.jpg` |
| `<角色>/views/body_{front,left,back,right}.png` | `素体/01～04_素体_*` |
| `<角色>/views/outfit_{front,left,back,right}.png` | `服装/01～04_服装_*` |
| `<角色>/views/hair_{front,left,back,right}.png` | `头发/01～04_头发_*` |
| `purple/views/outfit_sheet_final.png` | `紫色/服装/00_定稿基准图_图7四视角机能神级版.png` |
| `<角色>/model/body.glb` | `3D模型/01_素体_quad.glb` |
| `<角色>/model/outfit.glb` | `3D模型/02_服装_quad.glb` |
| `<角色>/model/hair.glb` | `3D模型/03_头发_quad.glb` |

**橙色例外**：原目录里 `02_服装_quad.glb` 实际是头发，`03_头发_quad.glb` 实际是服装。本目录已按内容改名：`orange/model/hair.glb` 来自 `02_服装_quad.glb`，`orange/model/outfit.glb` 来自 `03_头发_quad.glb`。

---

## 资产管理纪律

1. **不放临时文件**：`debug_*`、`crop_*`、`test_*`、`extract_*` 等调试产物写系统临时目录，用完删除，不提交。
2. **原画是造型基准**：白/橙/紫以 `characters/source/<角色>/poster/` 的主海报为准；Aster 以 `characters/aster/turnaround-final.png` 为准。外观由用户看图判断，不自报相似度。
3. **不放脚本**：`art/` 下不放 `.py`、`.sh`、`.bat` 等可执行脚本，批处理脚本统一放 `asternova/scripts/pipeline/`。
4. **预览只留有用的**：`render_previews/` 只放用于决策或验收的成图，不放草稿碎片。
