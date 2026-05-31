"use client";

import { FormEvent, useState } from "react";
import { BookmarkPlus, Send, X } from "lucide-react";
import html2canvas from "html2canvas";

import { Button } from "@/components/ui/button";
import { createFeatureMemory } from "@/lib/api";

function installScreenshotCompatibilityStyles() {
  const style = document.createElement("style");
  style.dataset.featureMemoryScreenshotStyle = "true";
  style.textContent = `
    .bg-background\\/80 {
      background-color: rgba(255, 255, 255, 0.8) !important;
    }

    .hover\\:bg-primary\\/90:hover {
      background-color: rgba(15, 15, 17, 0.9) !important;
    }

    .hover\\:bg-secondary\\/80:hover {
      background-color: rgba(244, 244, 245, 0.8) !important;
    }

    .hover\\:bg-destructive\\/90:hover {
      background-color: rgba(239, 68, 68, 0.9) !important;
    }

    .bg-green-600 {
      background-color: rgb(22, 163, 74) !important;
    }

    .hover\\:bg-green-700:hover {
      background-color: rgb(21, 128, 61) !important;
    }
  `;
  document.head.append(style);

  return () => style.remove();
}

async function capturePageScreenshot() {
  const removeCompatibilityStyles = installScreenshotCompatibilityStyles();

  try {
    return await html2canvas(document.body, {
      backgroundColor: null,
      ignoreElements: (element) => Boolean(element.closest("[data-feature-memory-ui]")),
      scale: Math.min(window.devicePixelRatio || 1, 2),
      useCORS: true,
      windowHeight: window.innerHeight,
      windowWidth: window.innerWidth,
    });
  } finally {
    removeCompatibilityStyles();
  }
}

export function FeatureMemoryButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function closeForm() {
    if (isSubmitting) {
      return;
    }
    setIsOpen(false);
    setError(null);
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const featureText = text.trim();
    setError(null);

    if (!featureText) {
      setError("Describe the feature before submitting.");
      return;
    }

    setIsSubmitting(true);

    try {
      const canvas = await capturePageScreenshot();

      await createFeatureMemory({
        text: featureText,
        page_url: window.location.href,
        page_title: document.title || null,
        screenshot_data_url: canvas.toDataURL("image/png"),
      });

      setText("");
      setIsOpen(false);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : "Unknown error";
      setError(`Failed to save feature: ${message}`);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="fixed right-4 top-4 flex max-w-[calc(100vw-2rem)] flex-col items-end gap-3"
      data-feature-memory-ui
    >
      <Button
        aria-expanded={isOpen}
        aria-label="Save feature"
        className="shadow-lg"
        type="button"
        onClick={() => setIsOpen(true)}
      >
        <BookmarkPlus data-icon="inline-start" />
        Carve it in
      </Button>

      {isOpen ? (
        <form
          className="w-80 max-w-full rounded-lg border bg-card p-4 shadow-lg"
          onSubmit={submitForm}
        >
          <div className="mb-3 flex items-start justify-between gap-3">
            <label className="text-sm font-semibold" htmlFor="feature-memory-text">
              What feature would you like to save?
            </label>
            <Button
              aria-label="Close form"
              size="sm"
              type="button"
              variant="ghost"
              onClick={closeForm}
            >
              <X data-icon="inline-start" />
            </Button>
          </div>

          <textarea
            className="min-h-32 w-full rounded-md border bg-background px-3 py-2 text-sm"
            disabled={isSubmitting}
            id="feature-memory-text"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />

          {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}

          <div className="mt-4 flex justify-end gap-2">
            <Button disabled={isSubmitting} type="button" variant="outline" onClick={closeForm}>
              Close
            </Button>
            <Button disabled={isSubmitting} type="submit">
              <Send data-icon="inline-start" />
              {isSubmitting ? "Carving..." : "Carve it in"}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
