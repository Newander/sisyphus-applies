"use client";

import { useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createPrompt, deletePrompt, updatePrompt, type Prompt } from "@/lib/api";

type NewPromptForm = {
  name: string;
  description: string;
  content: string;
};

const EMPTY_NEW_FORM: NewPromptForm = { name: "", description: "", content: "" };

export function PromptsEditor({ initialPrompts }: { initialPrompts: Prompt[] }) {
  const [prompts, setPrompts] = useState<Prompt[]>(initialPrompts);
  const [selectedId, setSelectedId] = useState<number | null>(
    initialPrompts.length > 0 ? initialPrompts[0].id : null,
  );
  const [isCreating, setIsCreating] = useState(false);
  const [newForm, setNewForm] = useState<NewPromptForm>(EMPTY_NEW_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const descriptionRef = useRef<HTMLInputElement>(null);
  const contentRef = useRef<HTMLTextAreaElement>(null);

  const selected = prompts.find((p) => p.id === selectedId) ?? null;

  async function handleSave() {
    if (!selected) return;
    setIsSaving(true);
    setError(null);

    try {
      const updated = await updatePrompt(selected.id, {
        description: descriptionRef.current?.value.trim() || null,
        content: contentRef.current?.value ?? selected.content,
      });
      setPrompts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(`Не удалось сохранить промпт: ${message}`);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCreate() {
    if (!newForm.name.trim() || !newForm.content.trim()) {
      setError("Название и содержимое обязательны");
      return;
    }
    setIsSaving(true);
    setError(null);

    try {
      const created = await createPrompt({
        name: newForm.name.trim(),
        description: newForm.description.trim() || null,
        content: newForm.content,
      });
      setPrompts((prev) => [...prev, created]);
      setSelectedId(created.id);
      setIsCreating(false);
      setNewForm(EMPTY_NEW_FORM);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(`Не удалось создать промпт: ${message}`);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(prompt: Prompt) {
    setError(null);

    try {
      await deletePrompt(prompt.id);
      const remaining = prompts.filter((p) => p.id !== prompt.id);
      setPrompts(remaining);
      if (selectedId === prompt.id) {
        setSelectedId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(`Не удалось удалить промпт: ${message}`);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
        <AppNav active="prompts" />
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-muted-foreground">Управление системными промптами</p>
          <h1 className="text-3xl font-semibold tracking-normal">Промпты</h1>
        </div>
      </header>

      {error ? (
        <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: prompt list */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Промпты
            </h2>
            <Button
              size="sm"
              type="button"
              variant="outline"
              onClick={() => {
                setIsCreating(true);
                setSelectedId(null);
                setNewForm(EMPTY_NEW_FORM);
                setError(null);
              }}
            >
              <Plus data-icon="inline-start" />
              Добавить
            </Button>
          </div>

          {prompts.length === 0 && !isCreating ? (
            <p className="text-sm text-muted-foreground">Промптов пока нет.</p>
          ) : null}

          {prompts.map((prompt) => (
            <button
              key={prompt.id}
              className={`w-full rounded-lg border p-4 text-left transition-colors hover:bg-accent ${
                selectedId === prompt.id && !isCreating
                  ? "border-primary bg-accent"
                  : "bg-card"
              }`}
              type="button"
              onClick={() => {
                setSelectedId(prompt.id);
                setIsCreating(false);
                setError(null);
              }}
            >
              <p className="font-medium">{prompt.name}</p>
              {prompt.description ? (
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                  {prompt.description}
                </p>
              ) : null}
            </button>
          ))}
        </div>

        {/* Right: editor */}
        <div className="lg:col-span-2">
          {isCreating ? (
            <Card>
              <CardHeader>
                <CardTitle>Новый промпт</CardTitle>
                <CardDescription>Заполните поля и нажмите «Создать»</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="new-name">Название</Label>
                    <Input
                      id="new-name"
                      placeholder="Уникальное имя промпта"
                      value={newForm.name}
                      onChange={(e) => setNewForm((f) => ({ ...f, name: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="new-description">Описание</Label>
                    <Input
                      id="new-description"
                      placeholder="Краткое описание (необязательно)"
                      value={newForm.description}
                      onChange={(e) => setNewForm((f) => ({ ...f, description: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="new-content">Содержимое</Label>
                    <Textarea
                      className="min-h-60 font-mono text-sm"
                      id="new-content"
                      placeholder="Текст промпта..."
                      value={newForm.content}
                      onChange={(e) => setNewForm((f) => ({ ...f, content: e.target.value }))}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setIsCreating(false);
                        setNewForm(EMPTY_NEW_FORM);
                        setError(null);
                        if (prompts.length > 0) setSelectedId(prompts[0].id);
                      }}
                    >
                      Отмена
                    </Button>
                    <Button
                      disabled={isSaving}
                      type="button"
                      onClick={() => void handleCreate()}
                    >
                      {isSaving ? "Создание…" : "Создать"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : selected ? (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex flex-col gap-1">
                    <CardTitle>{selected.name}</CardTitle>
                    <CardDescription className="text-xs">
                      Обновлён: {new Date(selected.updated_at).toLocaleString("ru-RU")}
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    type="button"
                    variant="destructive"
                    onClick={() => void handleDelete(selected)}
                  >
                    <Trash2 data-icon="inline-start" />
                    Удалить
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="edit-description">Описание</Label>
                    <Input
                      defaultValue={selected.description ?? ""}
                      id="edit-description"
                      key={`desc-${selected.id}`}
                      placeholder="Краткое описание (необязательно)"
                      ref={descriptionRef}
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="edit-content">Содержимое</Label>
                    <Textarea
                      className="min-h-60 font-mono text-sm"
                      defaultValue={selected.content}
                      id="edit-content"
                      key={`content-${selected.id}`}
                      ref={contentRef}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setIsCreating(true);
                        setSelectedId(null);
                        setNewForm(EMPTY_NEW_FORM);
                        setError(null);
                      }}
                    >
                      <Plus data-icon="inline-start" />
                      Добавить новый
                    </Button>
                    <Button
                      disabled={isSaving}
                      type="button"
                      onClick={() => void handleSave()}
                    >
                      {isSaving ? "Сохранение…" : "Сохранить"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex h-40 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              Выберите промпт слева или создайте новый
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
