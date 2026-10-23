# AsterNova 美术资产库（Art Assets）

> **定位**：原画、源模型、参考图与渲染预览。游戏实际加载的资产在 `client-godot-v2/` 内，这里放的是它们的来源和参考。

---

## 目录结构

```text
asternova/art/
├── README.md
├── characters/
│   ├── aster/          # Aster 设定：aster.md 人设档案、turnaround-final.png 定稿三视图、view_* 单视图、
│   │                   #             weapon.md 与 weapon-turnaround-final.png 佩刀「星霜月华」设定
│   └── source/         # 白/橙/紫三角色原始设定图与 AI 分件模型（只作参考，见其 README）
├── models/
│   ├── raw_ai_sculpt/  # Aster 的 Tripo 原始雕刻（静态参考，无骨骼）
│   ├── source/         # Tripo 源文件
│   ├── weapons/        # 佩刀 aster_katana 全套（游戏内用的是复制到 client-godot-v2/models/weapons/ 的 katana.glb）
│   ├── neighborhood/   # M1 街区源模型（街区、便利店、自动售货机），游戏里用的是 client-godot-v2 的副本
│   └── lumina_plaza/   # 旧光映广场源模型（游戏内已删除，留作素材）
├── references/         # 参考图（map_style/ 场景风格参考、便利店/售货机/地面/免费道具参考）
├── textures/           # .blend 源文件外链的贴图（改名或移动会让 .blend 丢贴图）
│   ├── nextgen_pbr/    #   M1 街区 modern_japan_neighborhood.blend 用
│   └── lumina_plaza/   #   光映广场 lumina_plaza_masterpiece.blend 用
├── ui/                 # 游戏界面资产
└── render_previews/    # 引擎实拍预览
    └── lighting/       # 四套光照预设实拍（docs/pipeline/lighting-guide.md）
```

---

## 资产管理纪律

1. **不放临时文件**：`debug_*`、`crop_*`、`test_*`、`extract_*` 等调试产物写系统临时目录，用完删除，不提交。
2. **原画是造型基准**：白/橙/紫以 `characters/source/<角色>/poster/` 的主海报为准；Aster 以 `characters/aster/turnaround-final.png` 为准。外观由用户看图判断，不自报相似度。
3. **不放脚本**：`art/` 下不放 `.py`、`.sh`、`.bat` 等可执行脚本，批处理脚本统一放 `asternova/scripts/pipeline/`。
4. **预览只留有用的**：`render_previews/` 只放用于决策或验收的成图，不放草稿碎片。
