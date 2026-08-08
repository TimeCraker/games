"use client"

import * as React from "react"

/**
 * Client-only: coarse mobile / tablet heuristic (UA + touch + pointer).
 */
export function detectMobileClient(): boolean {
  if (typeof window === "undefined") return false

  const ua = navigator.userAgent || ""
  if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet|SamsungBrowser|Kindle|Silk/i.test(ua)) {
    return true
  }

  const touchCapable = "ontouchstart" in window || (navigator.maxTouchPoints ?? 0) > 0
  if (touchCapable && typeof window.matchMedia === "function" && window.matchMedia("(pointer: coarse)").matches) {
    return true
  }

  return false
}

function isPortraitViewport(): boolean {
  if (typeof window === "undefined") return false
  return window.innerHeight > window.innerWidth
}

export type MobileGameViewport = {
  isMobile: boolean
  /** True when mobile and viewport is taller than wide (user should rotate). */
  isPortraitMobile: boolean
  shouldShowLandscapeHint: boolean
}

/** 尝试锁定横屏（部分 Android Chrome 在用户手势后可用；iOS 通常无效，需配合 CSS 旋转壳） */
export function tryLockLandscapeOrientation(): void {
  if (typeof window === "undefined") return
  try {
    const win = window as Window & { screen?: Screen & { orientation?: ScreenOrientation & { lock?: (o: OrientationLockType) => Promise<void> } } }
    const ori = win.screen?.orientation
    if (!ori?.lock) return
    void ori.lock("landscape-primary").catch(() => {
      /* unsupported or not allowed */
    })
  } catch {
    /* ignore unsupported env */
  }
}

/**
 * Tracks mobile detection and portrait vs landscape for arena / embedded games.
 */
export function useMobileGameViewport(): MobileGameViewport {
  const [isMobile, setIsMobile] = React.useState(false)
  const [isPortrait, setIsPortrait] = React.useState(false)

  React.useEffect(() => {
    const sync = () => {
      try {
        setIsMobile(detectMobileClient())
        setIsPortrait(isPortraitViewport())
      } catch {
        setIsMobile(false)
        setIsPortrait(false)
      }
    }

    sync()

    window.addEventListener("resize", sync)
    window.addEventListener("orientationchange", sync)

    const mql = typeof window.matchMedia === "function" ? window.matchMedia("(orientation: portrait)") : null
    const mqlAny = mql as (MediaQueryList & { addListener?: (cb: (e: MediaQueryListEvent) => void) => void; removeListener?: (cb: (e: MediaQueryListEvent) => void) => void }) | null

    if (mqlAny?.addEventListener) mqlAny.addEventListener("change", sync)
    else if (mqlAny?.addListener) mqlAny.addListener(sync)

    return () => {
      window.removeEventListener("resize", sync)
      window.removeEventListener("orientationchange", sync)
      if (mqlAny?.removeEventListener) mqlAny.removeEventListener("change", sync)
      else if (mqlAny?.removeListener) mqlAny.removeListener(sync)
    }
  }, [])

  const isPortraitMobile = isMobile && isPortrait

  return {
    isMobile,
    isPortraitMobile,
    shouldShowLandscapeHint: isPortraitMobile,
  }
}
