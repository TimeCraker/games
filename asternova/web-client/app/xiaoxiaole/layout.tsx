import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "桓睿消消乐",
  description: "轻松上头的三消小游戏",
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
