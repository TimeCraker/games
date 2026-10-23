# 光照方案与调参指南

适用于 `client-godot-v2` 的所有 3D 场景。写给不熟悉光照的人：照着做就能换天气、调亮暗，不需要改代码。

> **定位（2026-10-23 制作人确认）**：四套预设是光照**基线**，不是定死的数值。新场景建好后按该场景实际情况调（复制一份预设改，或直接改），调完重新出对比图给制作人看。不变的只有第 4 节的材质规则和"一个场景一个 LightingRig"的结构。

## 1. 结构：一个场景一个 LightingRig

光照由两样东西组成：

- **`LightingRig`**（`lighting/lighting_rig.gd`）：放进场景的一个节点。它会自动生成太阳（`Sun`，DirectionalLight3D）和环境（`WorldEnvironment`），不需要手动建这两个节点。
- **`LightingPreset`**（`lighting/presets/*.tres`）：一套完整参数，包括太阳、天空、环境光、曝光、全局光照、雾和辉光。换预设就是换天气和时段。

现有四套预设：

| 文件 | 名称 | 用途 |
| :--- | :--- | :--- |
| `day_clear.tres` | 晴天 · 清冷日光 | 默认白天，太阳 38° 高 |
| `golden_hour.tres` | 黄昏 · 低角度暖光 | 太阳 9°，长影子，暖色 |
| `overcast.tres` | 阴天 · 柔和漫射 | 几乎无直射光，影子很软 |
| `night_city.tres` | 夜晚 · 月光加街灯 | 冷色月光 + 招牌灯、店灯放大 |

参考场景：`scenes/levels/m1_street.tscn`。各预设的实拍效果在 `art/render_previews/lighting/`，每个预设两张：店内一张（带人偶，看角色受光），街道一张。

## 2. 日常操作

**在编辑器里换预设**：打开场景，选中 `LightingRig` 节点，在检查器里把 `Preset` 换成另一个 `.tres`。视口立即变化。

**调参数**：在检查器里点开 `Preset` 资源，直接拖滑块，视口实时更新。改动会存进那个 `.tres`，所有用这个预设的场景都会跟着变。

**做一套新预设**：在文件系统面板里复制一个最接近的 `.tres`，改名（例如 `rainy_evening.tres`），改 `Display Name`，再调参数。然后把它加进 `LightingRig` 的 `Presets` 列表。

**运行时对比**：运行场景后按 F1～F8，按 `Presets` 列表顺序切换（m1_street 里 F1 晴天、F2 黄昏、F3 阴天、F4 夜晚）。

**新场景接入**：往场景根节点下加一个 Node3D，挂 `lighting/lighting_rig.gd`，选一个预设。场景里不要再另放 WorldEnvironment 或 DirectionalLight3D，否则会和 Rig 打架。

**招牌灯、店内灯、路灯**：用 OmniLight3D 或 SpotLight3D 正常放，然后把它加入 `practical_light` 组（节点面板 → 组）。预设里的 `Practical Light Scale` 会按比例放大或缩小这些灯：白天 0.4（几乎看不出），夜晚 2.0。灯本身的 `Energy` 按"夜晚想要的亮度 ÷ 2"来设。

**出对比图**（改完预设后存档给别人看）：

```powershell
cd asternova
& "C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe" --path client-godot-v2 --resolution 1600x900 res://tests/lighting_preview.tscn -- --out=<输出目录>
```

可加 `--presets=day_clear,night_city` 只拍其中几套。机位和人偶站位在 `tests/lighting_preview_capture.gd` 顶部。

## 3. 参数速查：看到什么问题，调哪个

先调 **曝光**，再调 **太阳**，再调 **环境光**，最后才动雾和辉光。一次只改一个值，改完看图。

| 现象 | 调哪个参数 | 方向 |
| :--- | :--- | :--- |
| 整体太亮或太暗 | `Exposure` | 0.8～1.2 之间微调 |
| 受光面太亮、发白 | `Sun Energy` | 降 |
| 阴影里死黑 | `Ambient Energy` | 升 |
| 画面发灰发平、没有立体感 | `Ambient Energy` 降，`Sun Energy` 升 | 拉开亮暗差 |
| 影子边缘太硬 | `Sun Angular Size` | 升（阴天 3～4，晴天 0.5） |
| 影子方向不好看 | `Sun Azimuth` | 转太阳方向 |
| 想要长影子或夕阳感 | `Sun Elevation` | 降到 5～15 |
| 墙角、物体接地处不够"实" | `Ssao Intensity` | 升（1.5～2.5） |
| 远处太清楚、没有纵深 | `Fog Density` | 升（0.002～0.006） |
| 远处被雾吞掉、一片糊 | `Fog Density` / `Volumetric Fog Density` | 降 |
| 颜色太艳或太淡 | `Saturation` | 0.9～1.1 |
| 灯光周围光晕太大 | `Glow Threshold` 升或 `Glow Intensity` 降 | |
| 夜里灯不够亮 | `Practical Light Scale` | 升 |
| 角色和场景颜色不搭 | 先确认角色没有用自带固定底色的材质（见第 4 节） | |

各组参数的含义：

- **太阳 Sun**：方向（高度角、方位角）、颜色、强度、影子软硬。
- **天空 Sky**：天空颜色或一张 HDRI 全景图（填了 `Sky Panorama` 就用图）。天空同时决定环境光的颜色。
- **环境光 Ambient**：照不到太阳的地方有多亮。
- **曝光与色彩 Exposure**：相当于相机的曝光、对比度、饱和度。色调映射固定为 AgX。
- **全局光照 GI**：`SDFGI` 让光在场景里反弹，例如阳光照亮的墙会把颜色映到地面和角色身上。画面"有空气感"主要靠它，默认开。
- **AO / SSR**：接触阴影与屏幕空间反射（玻璃、湿地面）。
- **雾 Fog**：距离雾拉开纵深；体积雾能看到光柱，较耗性能，只在黄昏和夜晚开。
- **辉光 Glow**：亮的地方往外泛光。夜景招牌靠它。

## 4. 材质规则（光照调不准的头号原因）

场景材质必须让引擎算光照，否则无论预设怎么调，物体都不跟着变。

- **场景着色器（地面、建筑、道具）不写 `light()` 函数**。写了 `light()` 就等于自己接管光照，旧代码在里面加固定底色、乘 0.2 降权，结果是白天和夜晚亮度几乎一样。现在的 `toon_ground_pbr.gdshader`、`toon_prop.gdshader` 是普通 PBR，只做贴图、法线、粗糙度和自发光。
- **不用 `ambient_light_disabled`**。环境光、GI、反射都要从引擎拿。
- **角色着色器 `toon_character.gdshader` 可以写 `light()`**（二次元色阶需要），但暗部必须是"同一光源的一小份"，不能写固定颜色。环境光照常由引擎叠加。
- **自发光只用于真的会发光的东西**（招牌灯箱、屏幕、自动售货机橱窗），用遮罩贴图限定区域。

## 5. 后续：静态场景烘焙

现在用的是实时 SDFGI，好处是改了立刻看到。场景定稿后，静态建筑可以改用 **LightmapGI** 烘焙，画质更稳、运行更省：

1. 场景里加 `LightmapGI` 节点；静态网格导入时勾选 `Light Baking: Static Lightmaps`（会自动展第二套 UV）。
2. 选中 LightmapGI → 顶部 `Bake Lightmaps`。
3. 烘焙后关掉该场景预设里的 `Sdfgi Enabled`，角色等动态物体靠 LightmapGI 的探针受光。

换了太阳方向或时段要重新烘焙，所以只在光照定稿后做。

另外，需要镜面反射的区域（店面玻璃、室内）放 `ReflectionProbe`，开启 `Box Projection`，范围包住这个区域。m1_street 的店门口已有一个。
