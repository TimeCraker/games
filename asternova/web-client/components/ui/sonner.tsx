 "use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { HudCheck, HudInfo, HudWarn, HudError, HudSpinner } from "@/src/components/icons/arcade-icons"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <HudCheck className="size-4 text-hud-green" strokeWidth={1.6} />,
        info: <HudInfo className="size-4 text-hud-accent" strokeWidth={1.6} />,
        warning: <HudWarn className="size-4 text-hud-accent" strokeWidth={1.6} />,
        error: <HudError className="size-4 text-hud-red" strokeWidth={1.6} />,
        loading: <HudSpinner className="size-4 animate-spin text-hud-accent" strokeWidth={1.6} />,
      }}
      style={
        {
          "--normal-bg": "var(--ink-800)",
          "--normal-text": "var(--fog-100)",
          "--normal-border": "var(--ink-600)",
          "--border-radius": "0px",
        } as React.CSSProperties
      }
      toastOptions={{
        classNames: {
          toast: "cn-toast",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
