"use client";

import { RefreshCw } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { triggerReindex } from "@/lib/api";

export function ReindexButton() {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function handleClick() {
    setState("loading");
    try {
      await triggerReindex();
      setState("done");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }

  return (
    <Button
      disabled={state === "loading"}
      onClick={() => void handleClick()}
      variant={state === "error" ? "destructive" : "outline"}
    >
      <RefreshCw
        className={state === "loading" ? "animate-spin" : ""}
        data-icon="inline-start"
      />
      {state === "loading"
        ? "Starting..."
        : state === "done"
          ? "Reindex started"
          : state === "error"
            ? "Failed"
            : "Reindex all"}
    </Button>
  );
}
