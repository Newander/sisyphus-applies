"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiBaseUrl } from "@/lib/api";

export function GmailSyncButton() {
  const [isPending, setIsPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function sync() {
    setIsPending(true);
    setMessage(null);
    const response = await fetch(`${apiBaseUrl}/api/gmail/sync`, {
      method: "POST",
    });
    const body = await response.json().catch(() => null);
    setIsPending(false);

    if (!response.ok) {
      setMessage(body?.detail ?? "Sync failed");
      return;
    }

    setMessage(
      `Imported ${body.imported_count}, updated ${body.updated_count}, scanned ${body.scanned_count}. Refresh the page.`,
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <Button disabled={isPending} onClick={() => void sync()} type="button">
        <RefreshCw data-icon="inline-start" />
        {isPending ? "Syncing..." : "Sync now"}
      </Button>
      {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
    </div>
  );
}
