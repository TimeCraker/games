"use client"

import { GameBackButton } from "@/src/components/ui/GameBackButton"

export default function XiaoxiaolePage() {
  return (
    <div className="fixed inset-0 z-50 bg-space-black">
      <GameBackButton variant="floating" />
      <iframe
        src="/xiaoxiaole/index.html"
        title="桓睿消消乐"
        className="h-full w-full border-0"
        allow="autoplay; fullscreen"
      />
    </div>
  )
}
