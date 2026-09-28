/**
 * 弹珠风暴 —— 引擎公共契约（冻结版）。
 *
 * 本文件是引擎层与渲染 / UI 层的唯一接口约定：命名与字段一字不动，
 * 后续渲染美术、HUD、结算 UI 波次都按此对接。数值语义以
 * asternova/docs/shoot-them-all-whitepaper.md 为准。
 */

export type BallKind = "standard" | "blast" | "pierce" | "heavy"
export type PegKind = "crystal" | "resonance" | "bomb" // bomb 预留枚举，首发不做
export type ObstacleKind = "stone" | "ice"

export interface PegSpec {
  x: number
  y: number
  kind: PegKind
  hp?: number
}
export interface ObstacleSpec {
  x: number
  y: number
  w: number
  h: number
  kind: ObstacleKind
  hp: number
}

export interface LevelDef {
  id: number
  name: string // 中文关名，贴「深空观星台」母题，如「星环序曲」
  targetScore: number
  balls: BallKind[] // 长度=限球数；球组构成由关卡设计给定
  pegs: PegSpec[]
  obstacles: ObstacleSpec[]
}

export type StaPhase = "aiming" | "flying" | "resolving" | "level-clear" | "level-fail"

export interface StaHudState {
  phase: StaPhase
  levelId: number
  levelName: string
  score: number
  targetScore: number
  /** 未打出的球数（含即将打出的当前球） */
  ballsLeft: number
  /** 剩余球种队列（按打出顺序） */
  ballQueue: BallKind[]
  currentBall: BallKind | null
  combo: number
  bestCombo: number
  pegsLeft: number
  pegsTotal: number
  /** 0~1，用于进度条 */
  progress: number
  /** level-clear 时给出 1~3，其余阶段 0 */
  stars: number
}

export type EngineEvent =
  | { type: "launch"; ball: BallKind }
  | { type: "peg-broken"; x: number; y: number; kind: PegKind; score: number }
  | { type: "obstacle-hit"; x: number; y: number; kind: ObstacleKind; destroyed: boolean }
  | { type: "skill"; skill: "blast" | "pierce" | "heavy"; x: number; y: number }
  | { type: "combo"; value: number }
  | { type: "level-clear"; stars: number; score: number; ballsLeft: number }
  | { type: "level-fail"; score: number; targetScore: number }
