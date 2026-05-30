"use client";

import { Send, Terminal } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { AiLoader } from "@/components/ai-loader";
import { Button } from "@/components/ui/button";
import type { CodexStatus } from "@/lib/api";
import { askCodex } from "@/lib/api";
import { cn } from "@/lib/utils";

export function CodexPanel({ status }: { status: CodexStatus }) {
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
      setAnswer(response.answer || "Codex CLI вернул пустой ответ.");
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
          <legend className="text-sm font-medium">Режим</legend>
          <div className="flex w-fit rounded-md border bg-background p-1">
            <button
              className={cn(
                "h-9 rounded-sm px-3 text-sm font-medium",
                mode === "text" ? "bg-primary text-primary-foreground" : "text-muted-foreground",
              )}
              onClick={() => setMode("text")}
              type="button"
            >
              Текст
            </button>
            <button
              className={cn(
                "h-9 rounded-sm px-3 text-sm font-medium",
                mode === "url" ? "bg-primary text-primary-foreground" : "text-muted-foreground",
              )}
              onClick={() => setMode("url")}
              type="button"
            >
              Ссылка
            </button>
          </div>
        </fieldset>

        <label className="flex flex-col gap-2 text-sm font-medium">
          Вопрос
          <textarea
            className="min-h-40 resize-y rounded-md border bg-background px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
            maxLength={8000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Например: где в проекте создаются отклики?"
            required
            value={question}
          />
        </label>

        {mode === "url" ? (
          <label className="flex flex-col gap-2 text-sm font-medium">
            Ссылка для scrape
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
            Дополнительный контекст
            <textarea
              className="min-h-28 resize-y rounded-md border bg-background px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              maxLength={12000}
              onChange={(event) => setContext(event.target.value)}
              placeholder="Необязательно: вставь детали задачи, ошибку или ограничение."
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
            {isPending ? "Спрашиваю" : mode === "url" ? "Scrape и спросить" : "Спросить Codex"}
          </Button>
          {isPending ? (
            <span className="text-sm text-muted-foreground">CLI выполняется...</span>
          ) : null}
        </div>
      </form>

      <aside className="flex flex-col gap-3 rounded-lg border bg-muted p-4 text-sm">
        <div className="flex items-center gap-2 font-medium">
          <Terminal aria-hidden="true" />
          Локальный CLI
        </div>
        <dl className="flex flex-col gap-2 text-muted-foreground">
          <div className="flex flex-col gap-1">
            <dt className="font-medium text-foreground">Команда</dt>
            <dd className="break-all font-mono text-xs">{status.command.join(" ")}</dd>
          </div>
          <div className="flex flex-col gap-1">
            <dt className="font-medium text-foreground">Рабочая папка</dt>
            <dd className="break-all font-mono text-xs">{status.cwd}</dd>
          </div>
          <div className="flex flex-col gap-1">
            <dt className="font-medium text-foreground">Timeout</dt>
            <dd>{status.timeout_seconds} сек.</dd>
          </div>
        </dl>
      </aside>

      {(answer || error) && (
        <section className="lg:col-span-2">
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-base font-semibold tracking-normal">
              {error ? "Ошибка" : "Ответ Codex"}
            </h2>
            <pre className="mt-4 max-h-[32rem] overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-4 text-sm">
              {error || answer}
            </pre>
            {contextSource && !error ? (
              <p className="mt-3 break-all text-sm text-muted-foreground">
                Контекст: {contextSource}
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
