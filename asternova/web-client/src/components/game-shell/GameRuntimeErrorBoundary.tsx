"use client"

import * as React from "react"

type State = {
  hasError: boolean
  message: string
  stack: string
}

export class GameRuntimeErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = {
    hasError: false,
    message: "",
    stack: "",
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error?.message || "Unknown runtime error",
      stack: error?.stack || "",
    }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Keep console output for desktop debugging while also rendering details on mobile.
    console.error("[GameRuntimeErrorBoundary] runtime crash", error, info)
    this.setState((prev) => ({
      ...prev,
      stack: prev.stack || info.componentStack || "",
    }))
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="min-h-[100dvh] w-full overflow-auto bg-[#08090f] p-4 text-white">
        <div className="mx-auto max-w-4xl rounded-2xl border border-rose-300/30 bg-black/40 p-4 shadow-[0_20px_60px_rgba(0,0,0,0.55)]">
          <h1 className="text-lg font-semibold text-rose-200">小游戏运行异常</h1>
          <p className="mt-2 text-sm text-white/80">Application error: a client-side exception has occurred.</p>

          <div className="mt-4 rounded-xl border border-white/12 bg-black/45 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-white/45">Error Message</p>
            <pre className="mt-2 whitespace-pre-wrap break-words text-sm text-rose-200">{this.state.message}</pre>
          </div>

          <div className="mt-3 rounded-xl border border-white/12 bg-black/45 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-white/45">Stack Trace</p>
            <pre className="mt-2 max-h-[50dvh] overflow-auto whitespace-pre-wrap break-words text-xs text-white/80">
              {this.state.stack || "(no stack trace)"}
            </pre>
          </div>
        </div>
      </div>
    )
  }
}

