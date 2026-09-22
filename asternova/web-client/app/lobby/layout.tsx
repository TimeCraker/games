import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "游戏大厅",
  description: "选择小游戏进入 AsterNova 休闲大厅",
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
