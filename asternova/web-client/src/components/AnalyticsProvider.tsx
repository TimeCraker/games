"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { startHeartbeat, trackPageview } from "@/src/lib/analytics-client";
import { onIdle } from "@/src/lib/idle";

// 性能优化 2026-10：埋点不占加载关键路径——pageview 与心跳首拍都推迟到浏览器空闲期
// （fetch 本身异步，但避开 hydration 高峰期可减少带宽与主线程争抢）。
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    return onIdle(() => trackPageview(pathname || "/"), 3000);
  }, [pathname]);

  useEffect(() => {
    let heartbeatId: number | undefined;
    const cancel = onIdle(() => {
      heartbeatId = startHeartbeat();
    }, 4000);
    return () => {
      cancel();
      if (heartbeatId !== undefined) clearInterval(heartbeatId);
    };
  }, []);

  return <>{children}</>;
}
