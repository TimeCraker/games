"use client"

import * as React from "react"

type RuntimeErr = {
  message: string
  stack?: string
  source: "error" | "promise"
}

export function GlobalRuntimeErrorProbe() {
  const [runtimeErr, setRuntimeErr] = React.useState<RuntimeErr | null>(null)

  React.useEffect(() => {
    const onError = (event: ErrorEvent) => {
      const err = event.error as Error | undefined
      setRuntimeErr({
        source: "error",
        message: err?.message || event.message || "Unknown runtime error",
        stack: err?.stack || "",
      })
    }

    const onRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason as unknown
      if (reason instanceof Error) {
        setRuntimeErr({
          source: "promise",
          message: reason.message || "Unhandled promise rejection",
          stack: reason.stack || "",
        })
        return
      }
      setRuntimeErr({
        source: "promise",
        message: typeof reason === "string" ? reason : JSON.stringify(reason),
        stack: "",
      })
    }

    window.addEventListener("error", onError)
    window.addEventListener("unhandledrejection", onRejection)
    return () => {
      window.removeEventListener("error", onError)
      window.removeEventListener("unhandledrejection", onRejection)
    }
  }, [])

  if (!runtimeErr) return null

  return (
    <div className="fixed inset-0 z-[9999] overflow-auto bg-black/90 p-4 text-white">
      <div className="mx-auto max-w-4xl rounded-2xl border border-rose-300/35 bg-[#0c0d14] p-4">
        <h2 className="text-base font-semibold text-rose-200">Runtime Crash Captured ({runtimeErr.source})</h2>
        <p className="mt-3 text-xs uppercase tracking-[0.14em] text-white/45">Message</p>
        <pre className="mt-1 whitespace-pre-wrap break-words text-sm text-rose-100">{runtimeErr.message}</pre>
        <p className="mt-4 text-xs uppercase tracking-[0.14em] text-white/45">Stack</p>
        <pre className="mt-1 whitespace-pre-wrap break-words text-xs text-white/80">{runtimeErr.stack || "(no stack trace)"}</pre>
      </div>
    </div>
  )
}

