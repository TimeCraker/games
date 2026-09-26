import type { Metadata, Viewport } from "next"
import { LetsRunningPageClient } from "@/src/components/game-pages/LetsRunningPageClient"
import { ARCADE_BRAND, arcadeMetadataTitle } from "@/src/components/arcade/brand"

const brand = ARCADE_BRAND["lets-running"]

export const metadata: Metadata = {
  title: arcadeMetadataTitle("lets-running"),
  description: brand.tagline,
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function LetsRunningPage() {
  return <LetsRunningPageClient />
}
