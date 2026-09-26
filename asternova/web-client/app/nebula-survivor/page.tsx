import type { Metadata, Viewport } from "next"
import { NebulaSurvivorPageClient } from "@/src/components/game-pages/NebulaSurvivorPageClient"
import { ARCADE_BRAND, arcadeMetadataTitle } from "@/src/components/arcade/brand"

const brand = ARCADE_BRAND["nebula-survivor"]

export const metadata: Metadata = {
  title: arcadeMetadataTitle("nebula-survivor"),
  description: brand.tagline,
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function NebulaSurvivorPage() {
  return <NebulaSurvivorPageClient />
}
