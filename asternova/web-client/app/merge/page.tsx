import type { Metadata, Viewport } from "next"
import { MergePageClient } from "@/src/components/game-pages/MergePageClient"
import { ARCADE_BRAND, arcadeMetadataTitle } from "@/src/components/arcade/brand"

const brand = ARCADE_BRAND["merge"]

export const metadata: Metadata = {
  title: arcadeMetadataTitle("merge"),
  description: brand.tagline,
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function MergePage() {
  return <MergePageClient />
}
