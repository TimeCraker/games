# 桓睿消消乐 · HuanRui Match-3

立体三消游戏，纯前端实现（HTML + CSS + JS，零构建零依赖）。

🎮 **在线游玩**：<https://game.asterforge.top/xiaoxiaole/>

> 本 README 上半部分介绍这个游戏，下半部分是**通用游戏开发蓝图**——
> 沉淀本项目踩过的坑，列出"一个正常游戏该有哪些基础项"，
> 供以后做任何游戏时照着检查、补全。不局限于三消。

---

## 本游戏特性

- **立体棋盘** - CSS 3D 俯视（桌面端，移动端为性能关闭 3D 改 2D）
- **流畅动效** - DOM 持久化 + transform 定位，交换/下落/消除全动画
- **消除特效** - Canvas 粒子 + 飘字 + 连击屏闪（按设备质量分档）
- **真实音乐** - MP3 背景音乐列表，可切换，循环播放
- **合成音效** - Web Audio 交换/消除/连击/炸弹/通关音，零音频文件
- **游戏性** - 连击倍率、4 连炸弹、5 连彩虹、死局洗牌
- **12 关卡** - 前 3 关无限步数引导，后续递增难度
- **成就系统** - 12 个成就解锁通知
- **双主题** - 浅色/深色 + 3 套背景
- **响应式 + PWA** - 手机/电脑/横竖屏，可安装可离线

---

## 通用游戏开发蓝图

做任何网页/小游戏时，用这张清单逐项检查是否补全。每项 = 一个"正常游戏该有"的基础能力。

### 基础项清单

| 板块 | 是什么 | 为什么必须有 |
|---|---|---|
| **主菜单** | 游戏入口封面 | 第一印象，决定"像不像游戏" |
| **关卡/进度** | 关卡选择 + 解锁存档 | 给玩家目标感和持续动力 |
| **核心玩法** | 主操作循环 | 游戏的根，必须好玩且无 bug |
| **操作反馈** | 拖动跟手 + 音效 + 视觉 | 每次操作都要有即时回应 |
| **特效系统** | 粒子/飘字/震屏 | 让消除/得分有爽感 |
| **背景音乐** | 循环 BGM + 可切换 | 氛围感的核心，没有就空 |
| **音效** | 操作/消除/通关音 | 强化反馈，无声游戏很廉价 |
| **成就系统** | 解锁 + 通知 | 长线目标，增加粘性 |
| **设置面板** | 音量/音乐/动效/触觉 | 玩家可控，无障碍必须 |
| **主题/风格** | 浅色/深色 + 背景 | 视觉层次，适应环境 |
| **暂停/恢复** | 随时暂停 | 手机必备，防误操作 |
| **胜负界面** | 胜利/失败 + 星级 | 闭环反馈，驱动重玩 |
| **响应式** | 手机/电脑/横竖屏 | 全平台可玩 |
| **离线 PWA** | Service Worker 缓存 | 断网可玩，可安装 |
| **性能适配** | 按设备降级特效 | 低端机不卡，高端机好看 |

### 各板块实现要点

#### 主菜单
- 用**真实主视觉**（照片/插画/视频）做背景，不要纯文字海报
- 标题克制：大字号粗体即可，**不要霓虹灯渐变流动**（俗气）
- 主 CTA（开始游戏）+ 次级入口（关卡选择）+ 工具入口（设置/音效）
- 入场动效：元素错峰淡入，不要同时弹出

#### 关卡/进度
- localStorage 存：已解锁关卡、每关星级、最高分
- 前 1-3 关降低难度（无限步数/低目标），引导上手
- 关卡选择页可滚动，锁定的关卡灰显
- **平衡性**：第 1 关不能一步通关（目标分数要够高）

#### 核心玩法
- **DOM 持久化架构**：元素创建一次，位置变化只改 `transform`，CSS transition 产生动画（不要重建 DOM）
- 死局检测：无可行操作时自动洗牌，永不卡死
- 提示系统：idle 5 秒高亮一个可行操作
- 输入：滑动 + 点选双模式，移动端轻滑即触发（阈值 0.2 格 + 速度判断）

#### 操作反馈
- 拖动**即时跟手**（onMove 直接写 transform，不要 RAF 合帧，会延迟）
- 每次消除：音效 + 粒子 + 飘字 +（大连击）震屏
- 无效操作：摇头/回弹 + 提示音
- 移动端加 `navigator.vibrate` 触觉反馈

#### 特效系统
- 用**一个 Canvas + 粒子对象池**，不要每粒子建 DOM
- 粒子按需启动：无粒子时停止 RAF，不要永久空转
- **质量分档**：auto/high/medium/low，按 deviceMemory/hardwareConcurrency 自动选
- `prefers-reduced-motion` 永远覆盖为最低档
- 连击分档强调（3/5/8 连不同颜色），不要每次都全屏闪

#### 背景音乐
- 用 `<audio loop>` 播 MP3，默认循环第 1 首
- 设置面板可切换曲目（上一首/下一首 + 曲名）
- BGM 音量 = 总音量 × 0.55（比音效低，不刺耳）
- 暂停游戏时音乐暂停，恢复继续
- **音频 URL 加版本号** `bgm.mp3?v=2.16`，替换同名文件后强制刷新缓存
- 免费音乐源：Pixabay / OpenGameArt / FreePD / Free Music Archive（CC0 可商用）

#### 音效
- Web Audio API 合成（零文件、离线可用）
- 分类：选择/交换/消除/连击/炸弹/彩虹/胜利/失败/按钮/成就
- 连击音随 combo 升高音调
- 音量与 BGM 独立可控

#### 成就系统
- 定义成就表（首次操作/连击档/特殊方块/通关/累计）
- 触发时弹通知（图标 + 名称），3 秒自动消失
- localStorage 持久化已解锁

#### 设置面板
- 音效开关、音乐开关、音量滑块
- 动效开关、触觉开关
- 特效质量选择（自动/高/中/低）
- **从暂停弹窗也能进设置**（关闭设置时按状态恢复：playing 继续 / paused 回暂停弹窗）

#### 主题/风格
- CSS 变量驱动浅色/深色，一键切换 + 记忆
- 多套背景（纯色渐变/动态粒子/照片模糊）
- 移动端**移除 `backdrop-filter`** 毛玻璃（合成成本高），用纯色背景

#### 暂停/恢复
- 暂停时：停音乐、停提示计时、停动画循环、显弹窗
- 恢复时：按设置恢复音乐和动画
- **状态机要清晰**：menu/levels/intro/playing/paused，每个转移显式

#### 胜负界面
- 胜利：星级评定（按步数/分数）+ 下一关 + 重玩 + 回菜单
- 失败：分数展示 + 重玩 + 回菜单
- 模态框 `max-height:88vh + overflow-y:auto`，防小屏按钮点不到

#### 响应式
- 移动端单列布局，桌面端三列
- 触控目标 ≥ 44px
- 横屏手机单独适配（隐藏侧栏，棋盘居中）
- `env(safe-area-inset-*)` 尊重刘海/底部条

#### 离线 PWA
- Service Worker 缓存核心资源
- **HTML 用 network-first**（保证入口页最新），静态资源 stale-while-revalidate
- 新 SW 接管后 `controllerchange` 自动刷新页面（首次安装不刷新）
- 每次部署升缓存版本号 + 资源 URL 加版本查询参数

#### 性能适配（重要）
- **3D 棋盘在移动端关闭**：`preserve-3d` + 多层 `translateZ` 在手机是 GPU 杀手，桌面端才开
- Canvas DPR 封顶：移动 ≤1.5，桌面 ≤2（裸 devicePixelRatio 在 3× 手机是 9 倍像素）
- **永久 `will-change` 不要给所有元素**（64 个方块全开爆显存），只给活动状态
- 持续 `filter` 动画（hue-rotate/drop-shadow）在移动端停掉，改 transform/opacity
- `backdrop-filter:blur()` 移动端移除
- `pointermove` 跟手用即时写入（transform 是合成属性不触发 layout）
- 页面进后台 `visibilitychange` 停所有 RAF
- `ResizeObserver` 替代频繁 resize 监听

---

## 踩坑总结（本次教训）

1. **自动人脸裁剪不可信** - OpenCV 把草地/天空/衣服误检为脸。最终手动指定裁剪区域
2. **headless 桌面测不出手机卡顿** - 180fps 假象。要用 CPU 4× 限速 + 3× DPR 模拟
3. **3D 棋盘是手机卡顿元凶** - 不是 JS，是 64 个方块的 GPU 合成层。移动端关 3D 立刻流畅
4. **霓虹灯标题很土** - 渐变流动 + 流光 = 马路电灯牌。改克制大字 + 真实主视觉
5. **缓存更新是 SW 大坑** - 同名文件替换后 SW 仍给旧缓存。URL 加版本号才彻底解决
6. **状态机锁死** - 暂停→设置→关闭，state 卡 paused 无弹窗。关闭设置要按状态恢复
7. **RAF 合帧害跟手** - 拖动用 RAF 合帧引入 1 帧延迟，跟手交互要即时写入
8. **滑动阈值太重** - 0.35 格要滑很远。降到 0.22 + 速度判断，轻扫即触发
9. **图片无法多模态验证** - GLM 看不了图，裁剪/视觉判断必须交给多模态模型或用户

---

## 目录结构

```
public/                 # 部署目录（静态托管）
├── index.html          # 入口
├── styles.css          # 样式（双主题/响应式/动效）
├── game.js             # 游戏核心（架构/逻辑/特效/音效/成就）
├── sw.js               # Service Worker（离线缓存+自动更新）
├── manifest.webmanifest
└── assets/
    ├── faces/          # 方块照片（512×512）
    ├── backgrounds/    # 主视觉背景（WebP）
    └── music/          # 背景音乐 MP3（bgm1-4）
tools/
├── build_visual_assets.py  # 图片裁剪/主视觉生成
├── test.js                 # Playwright 功能测试
├── test_mobile_perf.js     # 移动端性能测试（CPU限速）
└── test_*.js               # 各专项测试
docs/
├── stages/             # 阶段开发记录
└── plans/              # 交给其他模型执行的计划
```

## 本地开发

```bash
# 生成图片素材（需 pillow）
python tools/build_visual_assets.py

# 起静态服务器
python -m http.server 8000 --directory public

# 功能测试（需 playwright + 系统 Chrome）
npm i -D playwright
node tools/test.js

# 移动端性能测试（CPU 4× 限速模拟）
node tools/test_mobile_perf.js
```

## 部署

静态文件部署到阿里云，Nginx 配置：

```nginx
location = /xiaoxiaole { return 301 /xiaoxiaole/; }
location /xiaoxiaole/ {
    alias /var/www/xiaoxiaole/;
    index index.html;
    try_files $uri $uri/ /xiaoxiaole/index.html;
}
```

文件位于 `/var/www/xiaoxiaole/`，复用 `game.asterforge.top` 的 SSL 证书。

```bash
# 部署命令
KEY=~/asterforge-deploy/ssh-keys/aliyun-ecs-login.pem
scp -F /dev/null -o StrictHostKeyChecking=no -i $KEY -r public/* root@8.162.7.172:/var/www/xiaoxiaole/
```

> 部署后**务必升 SW 缓存版本号**（`sw.js` 的 `CACHE` + `game.js` 的 `CACHE_VER`），
> 否则用户端不会及时更新。

## 技术栈

- 纯 HTML + CSS + JS（零构建、零依赖、零框架）
- Web Audio API（合成音效）
- Canvas 2D（粒子特效）
- Service Worker（离线 PWA）
- Playwright（自动化测试）

## License

游戏代码：MIT。背景音乐：CC0（来源 Pixabay / OpenGameArt）。
