"use client";

const SESSION_KEY = "tc_analytics_sid";

function getSessionId() {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function send(body: Record<string, unknown>) {
  const key = process.env.NEXT_PUBLIC_ANALYTICS_INGEST_KEY;
  if (!key) return;
  fetch(
    process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT ||
      "https://asterforge.top/api/analytics/ingest",
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Analytics-Key": key },
      body: JSON.stringify(body),
      keepalive: true,
    }
  ).catch(() => {});
}

export function trackPageview(path?: string) {
  const sessionId = getSessionId();
  const appId = process.env.NEXT_PUBLIC_ANALYTICS_APP_ID || "game";
  send({
    appId,
    events: [
      {
        appId,
        type: "pageview",
        path: path || window.location.pathname,
        sessionId,
      },
    ],
  });
}

export function startHeartbeat() {
  const sessionId = getSessionId();
  const appId = process.env.NEXT_PUBLIC_ANALYTICS_APP_ID || "game";
  const tick = () => send({ appId, heartbeat: { sessionId } });
  tick();
  return window.setInterval(tick, 30_000);
}
