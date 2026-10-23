# 占位人偶 + 标准动作库

作者：Quaternius。Universal Animation Library 免费 Standard 版，CC0 1.0。

- 作者与许可说明：https://quaternius.com/packs/universalanimationlibrary.html
- 官方下载页：https://quaternius.itch.io/universal-animation-library
- 本次取得的 GLTF 镜像：https://github.com/J-Ponzo/gltf-universal-animation-library
- 镜像保存的是 2025-06-10 免费版，不声称为最新版本。只使用包内实际存在的动作。
- 随附完整 `LICENSE.txt`。未使用付费 Pro / Source 内容。

## 在项目里的用途

- `scenes/entities/character_mannequin.tscn` 直接实例化 `mannequin.gltf`，挂 `CharacterRig`，作为玩家角色占位，保证战斗沙盒在正式角色做好之前能跑。
- 骨架是 Rigify 命名（`DEF-*`，52 骨），46 个动作。状态树里的旧剪辑名（`LightIdle`、`Slash1` 等）到人偶剪辑名（`Idle_Loop`、`Sword_Attack` 等）的映射在 `scripts/entities/player/character_rig.gd` 的 `CLIP_ALIASES`。
- 连招四段目前都映射到同一个 `Sword_Attack`，只是占位；正式连招动画到位后替换映射即可。
