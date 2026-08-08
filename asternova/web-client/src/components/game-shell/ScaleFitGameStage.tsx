"use client"

import * as React from "react"

type ScaleFitGameStageProps = {
  children: React.ReactNode
  defaultWidth?: number
  defaultHeight?: number
  className?: string
}

export function ScaleFitGameStage({
  children,
  defaultWidth = 1280,
  defaultHeight = 720,
  className,
}: ScaleFitGameStageProps) {
  const [scale, setScale] = React.useState(1)

  React.useEffect(() => {
    const updateScale = () => {
      const vw = window.visualViewport?.width ?? window.innerWidth
      const vh = window.visualViewport?.height ?? window.innerHeight
      const next = Math.min(vw / defaultWidth, vh / defaultHeight)
      setScale(Number.isFinite(next) && next > 0 ? next : 1)
    }

    updateScale()
    window.addEventListener("resize", updateScale)
    window.addEventListener("orientationchange", updateScale)
    window.visualViewport?.addEventListener("resize", updateScale)

    return () => {
      window.removeEventListener("resize", updateScale)
      window.removeEventListener("orientationchange", updateScale)
      window.visualViewport?.removeEventListener("resize", updateScale)
    }
  }, [defaultWidth, defaultHeight])

  return (
    <div
      className={className}
      style={{
        width: "100vw",
        height: "100dvh",
        overflow: "hidden",
        touchAction: "none",
        userSelect: "none",
        WebkitUserSelect: "none",
        WebkitTouchCallout: "none",
        overscrollBehavior: "none",
        position: "relative",
        background: "#000",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: `${defaultWidth}px`,
          height: `${defaultHeight}px`,
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center center",
          overflow: "hidden",
        }}
      >
        {children}
      </div>
    </div>
  )
}

