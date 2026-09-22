import type { Metadata, Viewport } from "next"
import { ShootThemAllPageClient } from "@/src/components/game-pages/ShootThemAllPageClient"

export const metadata: Metadata = {
  title: "射击大战",
  description: "俯视角弹幕射击，撑过一波波敌人",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function ShootThemAllPage() {
  return <ShootThemAllPageClient />
}
