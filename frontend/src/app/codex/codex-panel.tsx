"use client";

import { Send, Terminal } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { AiLoader } from "@/components/ai-loader";
import { Button } from "@/components/ui/button";
import type { LLMStatus } from "@/lib/api";
import { askCodex } from "@/lib/api";
import { cn } from "@/lib/utils";

export function CodexPanel({ status }: { status: LLMStatus }) {
  const [mode, setMode] = useState<"text" | "url">("text");
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [contextUrl, setContextUrl] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [contextSource, setContextSource] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isPending, setIsPending] = useState(false);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    const trimmedUrl = contextUrl.trim();
    if (!trimmedQuestion || isPending || (mode === "url" && !trimmedUrl)) {
      return;
    }

    setIsPending(true);
    setError("");
    setAnswer("");
    setContextSource("");
    setWarnings([]);

    try {
      const response = await askCodex(trimmedQuestion, mode, context.trim(), trimmedUrl);
      setAnswer(response.answer || "Codex CLI returned an empty response.");
      setContextSource(response.context_source);
      setWarnings(response.warnings);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Codex bridge failed");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <>
      <AiLoader isLoading={isPending} timeoutSeconds={status.timeout_seconds} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <form className="flex flex-col gap-4" onSubmit={submitQuestion}>
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium">Mode</legend>
          <div className="flex w-fit rounded-md border bg-background p-1">
            <button
              className={cn(
                "h-9 rounded-sm px-3 text-sm font-medium",
                mode === "text" ? "bg-primary text-primary-foreground" : "text-muted-foreground",
              )}
              onClick={() => setMode("text")}
              type="button"
            >
              Text
            </button>
            <button
              className={cn(
                "h-9 rounded-sm px-3 text-sm font-medium",
                mode === "url" ? "bg-primary text-primary-foreground" : "text-muted-foreground",
              )}
              onClick={() => setMode("url")}
              type="button"
            >
              URL
            </button>
          </div>
        </fieldset>

        <label className="flex flex-col gap-2 text-sm font-medium">
          Question
          <textarea
            className="min-h-40 resize-y rounded-md border bg-background px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
            maxLength={8000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="E.g.: where are applications created in the project?"
            required
            value={question}
          />
        </label>

        {mode === "url" ? (
          <label className="flex flex-col gap-2 text-sm font-medium">
            URL to scrape
            <input
              className="h-10 rounded-md border bg-background px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              maxLength={1000}
              onChange={(event) => setContextUrl(event.target.value)}
              placeholder="https://example.com/job"
              required
              type="url"
              value={contextUrl}
            />
          </label>
        ) : (
          <label className="flex flex-col gap-2 text-sm font-medium">
            Additional context
            <textarea
              className="min-h-28 resize-y rounded-md border bg-background px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              maxLength={12000}
              onChange={(event) => setContext(event.target.value)}
              placeholder="Optional: paste task details, an error, or a constraint."
              value={context}
            />
          </label>
        )}

        <div className="flex items-center gap-3">
          <Button
            disabled={isPending || !question.trim() || (mode === "url" && !contextUrl.trim())}
            type="submit"
          >
            <Send data-icon="inline-start" />
            {isPending ? "Asking" : mode === "url" ? "Scrape and ask" : "Ask Codex"}
          </Button>
          {isPending ? (
            <span className="text-sm text-muted-foreground">CLI is running...</span>
          ) : null}
        </div>
      </form>

      <aside className="flex flex-col gap-3 rounded-lg border bg-muted p-4 text-sm">
        <div className="flex items-center gap-2 font-medium">
          <Terminal aria-hidden="true" />
          {status.provider}
        </div>
        <dl className="flex flex-col gap-2 text-muted-foreground">
          {Object.entries(status.info).map(([key, value]) => (
            <div className="flex flex-col gap-1" key={key}>
              <dt className="capitalize font-medium text-foreground">{key}</dt>
              <dd className="break-all font-mono text-xs">{value}</dd>
            </div>
          ))}
          <div className="flex flex-col gap-1">
            <dt className="font-medium text-foreground">Timeout</dt>
            <dd>{status.timeout_seconds} sec.</dd>
          </div>
        </dl>
      </aside>

      {(answer || error) && (
        <section className="lg:col-span-2">
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-base font-semibold tracking-normal">
              {error ? "Error" : "Codex response"}
            </h2>
            <pre className="mt-4 max-h-[32rem] overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-4 text-sm">
              {error || answer}
            </pre>
            {contextSource && !error ? (
              <p className="mt-3 break-all text-sm text-muted-foreground">
                Context: {contextSource}
              </p>
            ) : null}
            {warnings.length > 0 && !error ? (
              <ul className="mt-3 flex flex-col gap-1 text-sm text-muted-foreground">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </div>
        </section>
      )}
      </div>
    </>
  );
}
