"use client";

import { useEffect, useState } from "react";

interface MessageTimeProps {
  timestamp: string | Date;
  className?: string;
}

/**
 * Client-only timestamp renderer to eliminate server/client hydration mismatches.
 * Renders an empty placeholder until mounted on the client, then displays formatted localized time.
 */
export function MessageTime({ timestamp, className }: MessageTimeProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <span className={className} suppressHydrationWarning>
        &nbsp;
      </span>
    );
  }

  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  const timeStr = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);

  return (
    <span className={className} suppressHydrationWarning>
      {timeStr}
    </span>
  );
}
