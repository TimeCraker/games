import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

// AsterNova 前端全局状态仓库：
// - 统一承载“登录态 + 大厅/房间 + 角色选择”等跨页面共享的数据（对应替代 Unity 的 DataManager/GameManager 的职责）
// - 使用 persist 将关键登录信息持久化到 localStorage，避免刷新页面丢失登录态
type GameState = {
  token: string;
  setToken: (token: string) => void;

  userId: number;
  setUserId: (userId: number) => void;

  username: string;
  setUsername: (username: string) => void;

  selectedClass: string;
  setSelectedClass: (selectedClass: string) => void;

  currentRoomId: string;
  setCurrentRoomId: (currentRoomId: string) => void;

  sessionReadyForBattle: boolean;
  setSessionReadyForBattle: (ready: boolean) => void;

  clearAuth: () => void;
};

export const useGameStore = create<GameState>()(
  persist(
    (set) => ({
      token: '',
      setToken: (token) => set({ token }),

      userId: 0,
      setUserId: (userId) => set({ userId }),

      username: '',
      setUsername: (username) => set({ username }),

      selectedClass: 'Role1_Speedster',
      setSelectedClass: (selectedClass) => set({ selectedClass }),

      currentRoomId: '',
      setCurrentRoomId: (currentRoomId) => set({ currentRoomId }),

      sessionReadyForBattle: false,
      setSessionReadyForBattle: (ready) => set({ sessionReadyForBattle: ready }),

      // 清空登录态（用于主动登出 / token 失效后的兜底）
      // 注意：由于本 store 开启了 persist，重置后的 token/userId 也会自动同步写回 localStorage
      clearAuth: () =>
        set({
          token: '',
          userId: 0,
          username: '',
          sessionReadyForBattle: false,
        }),
    }),
    {
      // localStorage 存储键名（可在浏览器 DevTools -> Application -> Local Storage 中查看）
      name: 'game-store',
      // 使用 localStorage 作为持久化介质（仅在浏览器环境可用）
      storage: createJSONStorage(() => localStorage),
      // 只持久化登录关键字段，避免把临时 UI/房间状态写入本地导致“脏状态”
      partialize: (state) => ({
        token: state.token,
        userId: state.userId,
        username: state.username,
        selectedClass: state.selectedClass,
        currentRoomId: state.currentRoomId,
      }),
    },
  ),
);

