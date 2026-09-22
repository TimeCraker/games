import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "登录",
  description: "AsterNova 账号登录、邮箱验证与游客模式",
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
