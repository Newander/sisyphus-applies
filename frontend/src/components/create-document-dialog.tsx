"use client";

import { FormEvent, useEffect, useState } from "react";
import { FilePlus2, Plus, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button, type ButtonProps } from "@/components/ui/button";
import { apiBaseUrl, createDocument, type Company } from "@/lib/api";

type CreateDocumentDialogProps = {
  triggerLabel?: string;
  triggerSize?: ButtonProps["size"];
  triggerVariant?: ButtonProps["variant"];
  iconOnly?: boolean;
};

type DocumentForm = {
  file_name: string;
  text: string;
  document_type: "cv" | "cover_letter" | "other";
  company_id: string;
  company_name: string;
  format: "md" | "docx";
};

const emptyForm: DocumentForm = {
  file_name: "",
  text: "",
  document_type: "cv",
  company_id: "",
  company_name: "",
  format: "md",
};

export function CreateDocumentDialog({
  triggerLabel = "Create document",
  triggerSize,
  triggerVariant,
  iconOnly = false,
}: CreateDocumentDialogProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [form, setForm] = useState<DocumentForm>(emptyForm);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    let isMounted = true;

    async function loadCompanies() {
      setIsLoadingCompanies(true);
      const response = await fetch(`${apiBaseUrl}/api/companies`);
      if (!isMounted) {
        return;
      }

      if (response.ok) {
        setCompanies(await response.json());
      }
      setIsLoadingCompanies(false);
    }

    void loadCompanies();

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  function closeDialog() {
    setIsOpen(false);
    setForm(emptyForm);
    setError(null);
    setIsSubmitting(false);
  }

  function updateCompanyName(value: string) {
    const company = companies.find(
      (item) => item.name.toLocaleLowerCase() === value.trim().toLocaleLowerCase(),
    );

    setForm((current) => ({
      ...current,
      company_id: company ? String(company.id) : "",
      company_name: value,
    }));
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const rawName = form.file_name.trim();
    const text = form.text.trim();
    if (!rawName || !text) {
      setError("Fill in the file name and document text");
      return;
    }

    const knownExtensions = [".md", ".txt", ".docx"];
    const hasExtension = knownExtensions.some((ext) => rawName.toLowerCase().endsWith(ext));
    const fileName = hasExtension ? rawName : `${rawName}.${form.format}`;

    setIsSubmitting(true);
    try {
      await createDocument({
        file_name: fileName,
        text,
        document_type: form.document_type,
        company_id: form.company_id ? Number(form.company_id) : null,
      });
      closeDialog();
      router.refresh();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to create document");
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Button
        aria-label={iconOnly ? triggerLabel : undefined}
        size={triggerSize}
        title={iconOnly ? triggerLabel : undefined}
        type="button"
        variant={triggerVariant}
        onClick={() => setIsOpen(true)}
      >
        {iconOnly ? <Plus aria-hidden="true" /> : <FilePlus2 data-icon="inline-start" />}
        {iconOnly ? null : triggerLabel}
      </Button>

      {isOpen ? (
        <div
          aria-modal="true"
          className="fixed inset-0 flex items-start justify-center overflow-y-auto bg-background/80 px-4 py-10 backdrop-blur-sm"
          role="dialog"
        >
          <div className="w-full max-w-3xl rounded-lg border bg-card shadow-lg">
            <div className="flex items-start justify-between gap-4 border-b p-5">
              <div className="flex flex-col gap-1">
                <h2 className="text-lg font-semibold tracking-normal">New document</h2>
                <p className="text-sm text-muted-foreground">
                  Saved as a .md or .docx file to the documents folder.
                </p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={closeDialog}>
                <X data-icon="inline-start" />
                Close
              </Button>
            </div>

            <form className="flex flex-col gap-4 p-5" onSubmit={submitForm}>
              {error ? (
                <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
                  {error}
                </div>
              ) : null}

              <div className="grid gap-4 md:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm font-medium">
                  File name
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    placeholder="My CV"
                    required
                    value={form.file_name}
                    onChange={(event) => setForm({ ...form, file_name: event.target.value })}
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Type
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.document_type}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        document_type: event.target.value as DocumentForm["document_type"],
                      })
                    }
                  >
                    <option value="cv">CV</option>
                    <option value="cover_letter">Cover letter</option>
                    <option value="other">Other</option>
                  </select>
                </label>
              </div>

              <div className="flex flex-col gap-2 text-sm font-medium">
                File format
                <div className="flex gap-2">
                  <button
                    type="button"
                    className={`rounded-md border px-4 py-1.5 text-sm transition-colors ${form.format === "md" ? "border-primary bg-primary text-primary-foreground" : "bg-background hover:bg-muted"}`}
                    onClick={() => setForm({ ...form, format: "md" })}
                  >
                    .md
                  </button>
                  <button
                    type="button"
                    className={`rounded-md border px-4 py-1.5 text-sm transition-colors ${form.format === "docx" ? "border-primary bg-primary text-primary-foreground" : "bg-background hover:bg-muted"}`}
                    onClick={() => setForm({ ...form, format: "docx" })}
                  >
                    .docx
                  </button>
                </div>
              </div>

              <label className="flex flex-col gap-2 text-sm font-medium">
                Company
                <input
                  className="h-10 rounded-md border bg-background px-3 text-sm"
                  disabled={isLoadingCompanies}
                  list="document-company-options"
                  placeholder="Optional"
                  value={form.company_name}
                  onChange={(event) => updateCompanyName(event.target.value)}
                />
                <datalist id="document-company-options">
                  {companies.map((company) => (
                    <option key={company.id} value={company.name} />
                  ))}
                </datalist>
                <span className="text-xs font-normal text-muted-foreground">
                  The link will be saved if a company is selected from the list.
                </span>
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium">
                Text
                <textarea
                  className="min-h-72 rounded-md border bg-background px-3 py-2 text-sm"
                  required
                  value={form.text}
                  onChange={(event) => setForm({ ...form, text: event.target.value })}
                />
              </label>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={closeDialog}>
                  Cancel
                </Button>
                <Button disabled={isSubmitting}>
                  <FilePlus2 data-icon="inline-start" />
                  {isSubmitting ? "Saving..." : "Save document"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
