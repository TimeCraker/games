# 桓睿消消乐 · HuanRui Match-3

立体三消游戏，纯前端实现（HTML + CSS + JS，零构建零依赖）。

🎮 **在线游玩**：<https://game.asterforge.top/xiaoxiaole/>

## 特性

- **立体棋盘** — CSS 3D `perspective + rotateX` 俯视，方块有厚度/高光/阴影
- **流畅动效** — DOM 持久化 + transform 定位，交换/下落/消除全动画（非重建 DOM）
- **消除特效** — Canvas 粒子爆炸 + 光环 + 飘字 `+分` / `COMBO×N` + 屏幕震动
- **Web Audio 音效** — 合成交换/消除/连击/炸弹/通关音，零音频文件、离线可用
- **游戏性** — 连击倍率、4 连生成「💣炸弹」(3×3 爆炸)、5 连生成「🌈彩虹」(清全场同款)
- **死局保护** — 检测无可行交换时自动洗牌，永不卡死
- **双主题** — 浅色 / 深色一键切换，记忆偏好
- **响应式** — 手机 / 电脑 / 横竖屏全适配，PWA 可安装
- **双输入** — 滑动方向交换 + 点选两次交换

## 技术要点

游戏从「重建 DOM」架构重构为「DOM 持久化 + transform 移动」，这是所有流畅动效的基础——
方块 DOM 只创建一次，位置变化只改 `transform: translate3d()`，CSS transition 自动产生动画。

## 目录结构

```
public/                 # 部署目录（静态托管）
├── index.html          # 入口
├── styles.css          # 样式（双主题/立体/响应式/动效）
├── game.js             # 游戏核心（架构/逻辑/特效/音效）
├── manifest.webmanifest
└── assets/faces/       # 方块照片（512×512，人脸居中裁剪）
tools/
├── crop_faces.py       # OpenCV 人脸检测 + 智能裁剪
└── test.js             # Playwright 自动化测试（系统 Chrome）
```

## 本地开发

```bash
# 裁剪照片（需 opencv-python + pillow）
python tools/crop_faces.py

# 起静态服务器
python -m http.server 8000 --directory public

# 自动化测试（需 playwright，用系统 Chrome）
npm i -D playwright
node tools/test.js
```

## 部署

静态文件部署到阿里云边缘节点，Nginx 配置：

```nginx
location = /xiaoxiaole { return 301 /xiaoxiaole/; }
location /xiaoxiaole/ {
    alias /var/www/xiaoxiaole/;
    index index.html;
    try_files $uri $uri/ /xiaoxiaole/index.html;
}
```

文件位于 `/var/www/xiaoxiaole/`，复用 `game.asterforge.top` 的 SSL 证书。
