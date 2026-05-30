"use client";

import { useEffect, useState } from "react";

type AiLoaderProps = {
  isLoading: boolean;
  timeoutSeconds?: number;
};

export function AiLoader({ isLoading, timeoutSeconds = 120 }: AiLoaderProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setElapsed(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isLoading) {
    return null;
  }

  const remaining = Math.max(0, timeoutSeconds - elapsed);
  const progress = Math.min(100, (elapsed / timeoutSeconds) * 100);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex w-80 flex-col gap-4 rounded-xl border bg-card p-6 shadow-lg">
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-primary" />
          </span>
          <p className="text-base font-semibold">Ждём Codex...</p>
        </div>

        <div className="flex flex-col gap-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-1000"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>+{elapsed}с</span>
            <span>осталось ~{remaining}с</span>
          </div>
        </div>
      </div>
    </div>
  );
}
