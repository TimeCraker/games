import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "竞技场",
  description: "AsterNova 双人对战竞技场",
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
