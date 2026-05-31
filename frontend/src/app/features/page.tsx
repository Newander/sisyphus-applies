"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { Eye, Pencil, X } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  closeFeatureMemory,
  getFeatureMemoriesPage,
  updateFeatureMemory,
  type FeatureMemory,
} from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function FeaturesPage() {
  const [features, setFeatures] = useState<FeatureMemory[]>([]);
  const [totalFeatures, setTotalFeatures] = useState(0);
  const [selectedFeature, setSelectedFeature] = useState<FeatureMemory | null>(null);
  const [editingFeature, setEditingFeature] = useState<FeatureMemory | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const editTextRef = useRef<HTMLTextAreaElement>(null);
  const editTitleRef = useRef<HTMLInputElement>(null);

  const columns = useMemo<DataTableColumn<FeatureMemory>[]>(
    () => [
      {
        id: "created_at",
        header: "Date",
        accessor: "created_at",
        className: "text-muted-foreground",
        sortValue: (feature) => new Date(feature.created_at),
        cell: (feature) => formatDate(feature.created_at),
      },
      {
        id: "text",
        header: "Feature",
        accessor: "text",
        className: "max-w-md",
        cell: (feature) => <p className="line-clamp-2">{feature.text}</p>,
      },
      {
        id: "page_url",
        header: "Page",
        sortValue: (feature) => feature.page_title ?? feature.page_url,
        className: "max-w-sm",
        cell: (feature) => (
          <a
            className="block truncate text-sm text-primary underline-offset-4 hover:underline"
            href={feature.page_url}
            rel="noreferrer"
            target="_blank"
          >
            {feature.page_title ?? feature.page_url}
          </a>
        ),
      },
    ],
    [],
  );

  const loadFeatures = useCallback(async (query: DataTableQuery) => {
    setIsLoading(true);
    setError(null);

    try {
      const page = await getFeatureMemoriesPage({
        direction: query.sort?.direction ?? "desc",
        page: query.page,
        pageSize: query.pageSize,
        sort: query.sort?.columnId ?? "created_at",
      });
      setFeatures(page.items);
      setTotalFeatures(page.total);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "Unknown error";
      setError(`Failed to load saved features: ${message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  async function saveFeature() {
    if (!editingFeature) return;
    setIsSaving(true);
    setError(null);

    try {
      const updated = await updateFeatureMemory(editingFeature.id, {
        text: editTextRef.current?.value ?? editingFeature.text,
        page_title: editTitleRef.current?.value.trim() || null,
      });
      setFeatures((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setEditingFeature(null);
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "Unknown error";
      setError(`Failed to save feature: ${message}`);
    } finally {
      setIsSaving(false);
    }
  }

  async function closeFeature(feature: FeatureMemory) {
    setError(null);

    try {
      await closeFeatureMemory(feature.id);
      setFeatures((current) => current.filter((item) => item.id !== feature.id));
      setTotalFeatures((current) => Math.max(0, current - 1));
      if (selectedFeature?.id === feature.id) {
        setSelectedFeature(null);
      }
    } catch (closeError) {
      const message = closeError instanceof Error ? closeError.message : "Unknown error";
      setError(`Failed to close feature: ${message}`);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="features" />
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Ideas saved from the screen</p>
            <h1 className="text-3xl font-semibold tracking-normal">Features</h1>
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Saved features</CardTitle>
            <CardDescription>{features.length} open features in the local database.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={columns}
              data={features}
              emptyMessage="No open features yet."
              initialSort={{ columnId: "created_at", direction: "desc" }}
              isLoading={isLoading}
              onQueryChange={loadFeatures}
              rowKey={(feature) => feature.id}
              totalItems={totalFeatures}
              renderActions={(feature) => (
                <>
                  <Button
                    size="icon"
                    title="View"
                    type="button"
                    variant="outline"
                    onClick={() => setSelectedFeature(feature)}
                  >
                    <Eye />
                  </Button>
                  <Button
                    size="icon"
                    title="Edit"
                    type="button"
                    variant="outline"
                    onClick={() => setEditingFeature(feature)}
                  >
                    <Pencil />
                  </Button>
                  <Button
                    size="icon"
                    title="Let it roll"
                    type="button"
                    variant="destructive"
                    onClick={() => void closeFeature(feature)}
                  >
                    <X />
                  </Button>
                </>
              )}
            />
          </CardContent>
        </Card>
      </div>

      {editingFeature ? (
        <div
          aria-modal="true"
          className="fixed inset-0 flex items-start justify-center overflow-y-auto bg-background/80 px-4 py-10 backdrop-blur-sm"
          role="dialog"
        >
          <div className="w-full max-w-2xl rounded-lg border bg-card shadow-lg">
            <div className="flex items-start justify-between gap-4 border-b p-5">
              <h2 className="text-lg font-semibold tracking-normal">Edit feature</h2>
              <Button
                aria-label="Cancel editing"
                size="sm"
                type="button"
                variant="ghost"
                onClick={() => setEditingFeature(null)}
              >
                <X data-icon="inline-start" />
              </Button>
            </div>
            <div className="flex flex-col gap-5 p-5">
              <div className="flex flex-col gap-2">
                <Label htmlFor="edit-page-title">Page title</Label>
                <Input
                  defaultValue={editingFeature.page_title ?? ""}
                  id="edit-page-title"
                  placeholder="Page title (optional)"
                  ref={editTitleRef}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="edit-text">Feature text</Label>
                <Textarea
                  className="min-h-40"
                  defaultValue={editingFeature.text}
                  id="edit-text"
                  ref={editTextRef}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditingFeature(null)}
                >
                  Cancel
                </Button>
                <Button
                  disabled={isSaving}
                  type="button"
                  onClick={() => void saveFeature()}
                >
                  {isSaving ? "Saving…" : "Save"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {selectedFeature ? (
        <div
          aria-modal="true"
          className="fixed inset-0 flex items-start justify-center overflow-y-auto bg-background/80 px-4 py-10 backdrop-blur-sm"
          role="dialog"
        >
          <div className="w-full max-w-5xl rounded-lg border bg-card shadow-lg">
            <div className="flex items-start justify-between gap-4 border-b p-5">
              <div className="flex flex-col gap-1">
                <h2 className="text-lg font-semibold tracking-normal">Saved feature</h2>
                <p className="break-all text-sm text-muted-foreground">
                  {selectedFeature.page_url}
                </p>
              </div>
              <Button
                aria-label="Close preview"
                size="sm"
                type="button"
                variant="ghost"
                onClick={() => setSelectedFeature(null)}
              >
                <X data-icon="inline-start" />
              </Button>
            </div>
            <div className="flex flex-col gap-5 p-5">
              <p className="whitespace-pre-wrap text-sm">{selectedFeature.text}</p>
              <img
                alt="Page screenshot for saved feature"
                className="w-full rounded-md border"
                src={selectedFeature.screenshot_data_url}
              />
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
