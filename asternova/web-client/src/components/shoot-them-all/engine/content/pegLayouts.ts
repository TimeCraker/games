import { HEIGHT, WIDTH } from "../../constants"

/** 钉子布局生成（M1 基础版：青色晶体簇）。
 *  后续 #5/#7 接入 7 类钉子 + 节点种子化生成（Stage Spec §3.7/§4.4）。 */
export interface PegSpec {
  x: number
  y: number
  kind: "peg-crystal"
}

/**
 * 生成一簇普通晶体（六边形错位排布），位于画布中下区域。
 * ~24 颗，间距 56，给 60% 清除过关留余量。
 */
export function generateCrystalCluster(): PegSpec[] {
  const pegs: PegSpec[] = []
  const cols = 6
  const rows = 4
  const spacing = 56
  const startX = WIDTH / 2 - ((cols - 1) * spacing) / 2
  const startY = HEIGHT * 0.42
  for (let r = 0; r < rows; r++) {
    const offset = r % 2 === 1 ? spacing / 2 : 0
    for (let c = 0; c < cols; c++) {
      const x = startX + c * spacing + offset
      const y = startY + r * spacing * 0.92
      // 边界内收，避免贴墙
      if (x < 60 || x > WIDTH - 60) continue
      pegs.push({ x, y, kind: "peg-crystal" })
    }
  }
  return pegs
}
