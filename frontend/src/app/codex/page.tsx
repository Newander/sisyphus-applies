import { AppNav } from "@/components/app-nav";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCodexStatus } from "@/lib/api";

import { CodexPanel } from "./codex-panel";

export default async function CodexPage() {
  const status = await getCodexStatus();

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="codex" />
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Ask, and it shall answer</p>
            <h1 className="text-3xl font-semibold tracking-normal">The Oracle</h1>
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Ask the Oracle</CardTitle>
            <CardDescription>
              Pose your question. The Oracle consults the local LLM and speaks its answer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CodexPanel status={status} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
