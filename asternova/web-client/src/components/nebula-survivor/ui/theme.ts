/** 品级工艺（白皮书 §5.2）：颜色只是标识，**档次靠工艺单调**读出 */
export const TIERS = [
  { hex: "#F2F4F5", label: "普通", stars: 1 },
  { hex: "#9CB86A", label: "优秀", stars: 2 },
  { hex: "#8FB3C9", label: "稀有", stars: 3 },
  { hex: "#D8A33C", label: "传说", stars: 4 },
  { hex: "#C0503A", label: "神话", stars: 5 },
] as const

export function tierOf(stars: number) {
  return TIERS[Math.max(0, Math.min(TIERS.length - 1, stars - 1))]
}

/** 工艺编码：1★ 细边无光 → 5★ 粗边 + 外辉光 + 流光 */
export function tierStyle(stars: number): React.CSSProperties {
  const { hex } = tierOf(stars)
  const s = Math.max(1, Math.min(5, stars))
  const borderW = s <= 2 ? 1 : s === 3 ? 1.5 : 2
  const borderA = s === 1 ? 0.12 : s === 2 ? 0.35 : s === 3 ? 0.55 : s === 4 ? 0.7 : 0.85
  const base: React.CSSProperties = {
    borderWidth: borderW,
    borderStyle: "solid",
    borderColor: s === 1 ? "rgba(255,255,255,0.12)" : hexToRgba(hex, borderA),
    background: s === 1 ? "rgba(17,19,22,0.82)" : hexToRgba(hex, 0.10),
  }
  if (s >= 3) base.boxShadow = `inset 0 0 14px ${hexToRgba(hex, 0.18)}`
  if (s >= 4) base.boxShadow = `0 0 20px ${hexToRgba(hex, 0.28)}, inset 0 0 14px ${hexToRgba(hex, 0.14)}`
  if (s >= 5) base.boxShadow = `0 0 26px ${hexToRgba(hex, 0.42)}, inset 0 0 16px ${hexToRgba(hex, 0.20)}`
  return base
}

export function hexToRgba(hex: string, a: number): string {
  const h = hex.replace("#", "")
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}

/** 等宽读数（HUD 数据层统一字体） */
export const MONO = "font-mono-data tabular-nums"
