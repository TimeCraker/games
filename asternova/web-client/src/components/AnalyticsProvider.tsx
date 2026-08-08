"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { startHeartbeat, trackPageview } from "@/src/lib/analytics-client";

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    trackPageview(pathname || "/");
  }, [pathname]);

  useEffect(() => {
    const id = startHeartbeat();
    return () => clearInterval(id);
  }, []);

  return <>{children}</>;
}
