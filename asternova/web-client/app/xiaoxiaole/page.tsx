"use client"

import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"

export default function XiaoxiaolePage() {
  const router = useRouter()
  return (
    <div className="fixed inset-0 z-50 bg-[#0a0a0f]">
      <button
        onClick={() => router.push("/lobby")}
        className="absolute left-3 top-3 z-10 flex items-center gap-1.5 rounded-full border border-white/15 bg-black/40 px-3.5 py-2 text-[13px] font-medium text-white/90 backdrop-blur-md transition hover:bg-black/60"
      >
        <ArrowLeft className="h-4 w-4" strokeWidth={2} />
        返回大厅
      </button>
      <iframe
        src="/xiaoxiaole/index.html"
        title="桓睿消消乐"
        className="h-full w-full border-0"
        allow="autoplay; fullscreen"
      />
    </div>
  )
}
