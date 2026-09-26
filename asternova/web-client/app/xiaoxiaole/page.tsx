"use client"

import { arcadeDisplayName } from "@/src/components/arcade/brand"
import { GameBackButton } from "@/src/components/ui/GameBackButton"

const TITLE = arcadeDisplayName("xiaoxiaole")

export default function XiaoxiaolePage() {
  return (
    <main id="main-content" tabIndex={-1} className="fixed inset-0 z-50 bg-space-black">
      <h1 className="sr-only">{TITLE}</h1>
      <iframe
        src="/xiaoxiaole/index.html"
        title={TITLE}
        className="h-full w-full border-0"
        allow="autoplay; fullscreen"
      />
      <GameBackButton variant="floating" />
    </main>
  )
}