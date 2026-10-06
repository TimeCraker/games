# Audio Asset Layout

Place all background music (BGM) and scene music files under this directory.

Suggested naming:
- `bgm-main.*`
- `bgm-lobby.*`
- `bgm-loop.*`

Structure:
- `public/audio/home/` - home page music
- `public/audio/lobby/` - lobby music
- `public/audio/games/` - in-game music by route
  - `shoot-them-all/`
  - `lets-running/`
  - `merge/`
  - `nebula-survivor/`
  - `arena/`
  - (`xiaoxiaole/` 路由已上线，音频目录按需增补)

When referenced in code, use absolute public paths like:
- `/audio/home/bgm-main.mp3`
- `/audio/lobby/bgm-lobby.mp3`
- `/audio/games/merge/bgm-loop.mp3`
