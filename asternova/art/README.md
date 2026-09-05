# AsterNova 美术资产库（Art Assets）

> **定位**：AsterNova 游戏本体的核心美术与原画源资产大门。所有角色定稿原画、三视图基准、官方对比图与引擎真机渲染件存放于此。

---

## 目录结构

```text
asternova/art/
├── README.md                  # 资产库索引与管理规范
├── characters/                # 角色全量自包含资产库
│   └── aster/                 # 女主角 Aster 专档包
│       ├── aster.md                   # 📝 人设档案 / 身材数值 / 生图提示词
│       ├── turnaround-final.png       # ✅ 官方角色定稿三视图（正/侧/背，建模与验收绝对基准）
│       ├── weapon.md                  # 🗡️ Aster 专属佩刀「星霜月华」美术专档（3D 资产与检视指引）
│       ├── weapon-turnaround-final.png # 🗡️ Aster 专属佩刀「星霜月华」定稿全部分件设定图
│       ├── turnaround-v1.png          # 历史备选版本
│       ├── turnaround-jk-rejected.png # 历史否决版本（JK 水手服，留档防走样）
│       ├── view_front.png             # 正面参考视图片
│       ├── view_side.png              # 侧面参考视图片
│       └── view_back.png              # 背面参考视图片
│
├── comparisons/               # 官方 2D 原画 vs 3D 渲染多视点同框验收对比图
│   ├── compare_front.png              # 正面 1:1 对齐对比
│   ├── compare_side.png               # 侧颜轮廓对比
│   ├── compare_back.png               # 背影与发流对比
│   └── compare_closeup.png            # 面部特写对比
│
└── render_previews/           # 唯一权威真机渲染件（Godot 4.7 引擎捕获与 Blender 阶段验收）
    ├── characters/            # 角色阶段验收与正式定稿展示
    │   └── aster/             # Aster 正式全身/特写/三视角 2K 成图 (13 张)
    └── scenes/                # 场景工业化验收成图
        ├── golden_slice/      # 黄金切片街景 4K 级细节图 (4 张)
        ├── modular_kit/       # 终末地级模块化单体与全景图 (5 张)
        ├── playtest/          # 6 大机位实机沙盒动线检验图 (6 张)
        ├── stage_inspection/  # 阶段巡检视察图 (9 张)
        ├── screenshot_high.png # 高画质展示图（全后处理/光照）
        ├── screenshot_medium.png # 中画质展示图（平衡档）
        ├── screenshot_low.png  # 低画质基准图（核显/锁 60 FPS）
        └── screenshot_street_wide.png # 黄昏樱花商店街全景展示
```

---

## 资产管理纪律

1. **绝对整洁原则**：
   - 严禁在 `art/` 根目录及子目录随意堆放 `debug_*`、`crop_*`、`test_*`、`extract_*` 等临时脚本调试图片。
   - 建模调试、UV 裁剪、贴图提取的中间临时文件必须写入系统临时目录或内存，调试完毕立即清除，不得提交进 `art/`。
2. **唯一权威真理源（SSOT）**：
   - 角色建模与风格验收以 `characters/aster/turnaround-final.png` 为唯一视觉基准。
   - 真机与阶段渲染验收图唯一存放在 `art/render_previews/`，严禁在其他工程（如 `render-lab/`）建立并行的截图目录。
3. **脚本绝对隔离纪律（Script Segregation）**：
   - **`art/` 目录永久禁止存放任何可执行脚本（`.py`, `.sh`, `.bat` 等）**。
   - 所有模型重拓扑、烘焙、材质生成与批处理流水线脚本，必须统一收敛在 `asternova/scripts/pipeline/` 或 `asternova/scripts/` 下维护。
4. **成果存档规范**：
   - `render_previews/` 仅保留具有里程碑验收意义的高清成图，杜绝未成型的草稿碎片入库。


