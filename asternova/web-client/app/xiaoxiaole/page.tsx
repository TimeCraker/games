"use client"

import { GameBackButton } from "@/src/components/ui/GameBackButton"

export default function XiaoxiaolePage() {
  return (
    <main id="main-content" tabIndex={-1} className="fixed inset-0 z-50 bg-space-black">
      <h1 className="sr-only">桓睿消消乐</h1>
      <iframe
        src="/xiaoxiaole/index.html"
        title="桓睿消消乐"
        className="h-full w-full border-0"
        allow="autoplay; fullscreen"
      />
      <GameBackButton variant="floating" />
    </main>
  )
}