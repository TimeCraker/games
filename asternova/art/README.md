# AsterNova 美术资产库（Art Assets）

> **定位**：AsterNova 游戏本体的核心美术与原画源资产大门。所有角色原画、三视图、3D 模型、场景原画与 UI 贴图全部存放于此。

---

## 目录结构

```text
asternova/art/
├── characters/                # 角色美术资产
│   └── aster/                 # 女主角 Aster 专档
│       ├── turnaround-final.png       # ✅ 官方定稿三视图（正/侧/背，建模基准）
│       ├── turnaround-v1.png          # 备选版本
│       └── turnaround-jk-rejected.png # 历史否决版本
│
├── environments/              # 场景美术资产（黄昏樱花商店街原画、贴图、模型）
└── ui/                        # 游戏内 HUD、手柄图标、界面视觉素材
```

## 规范

- **三视图与设计稿**：存放于对应角色子目录 `characters/<name>/`；
- **纯文本设定与提示词**：存放于 `asternova/docs/characters/<name>/`，与美术二进制资产清晰解耦。
