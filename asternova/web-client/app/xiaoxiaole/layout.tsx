import type { Metadata } from "next"
import type { ReactNode } from "react"

import { ARCADE_BRAND, arcadeMetadataTitle } from "@/src/components/arcade/brand"

const brand = ARCADE_BRAND["xiaoxiaole"]

export const metadata: Metadata = {
  title: arcadeMetadataTitle("xiaoxiaole"),
  description: brand.tagline,
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
