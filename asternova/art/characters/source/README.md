# 三角色原始美术源

白、橙、紫三个角色最原始的设定图与 AI 生成模型，2026-10-23 从本机 `C:\Users\TimeCraker\Pictures\游戏人物建模参考\<白色|橙色|紫色>\` 复制入库，内容未做任何修改。本机原目录保持不动；各子目录里的 `归档_旧版备选`、`备选参考_*` 过程稿没有复制。

这些是**参考资料**，不是可直接进游戏的角色：三个 GLB 是 Tripo 分件生成的静态网格，没有骨骼和权重，部件之间尺度不对应。制作正式角色的方法见 [`docs/pipeline/character-pipeline.md`](../../../docs/pipeline/character-pipeline.md)。

## 文件对应

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
