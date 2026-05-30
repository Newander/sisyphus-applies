"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Code2, Pencil, Plus, Save, WandSparkles, X } from "lucide-react";

import { AiLoader } from "@/components/ai-loader";
import { Button, type ButtonProps } from "@/components/ui/button";
import { SearchableSelect } from "@/components/ui/searchable-select";
import {
  apiBaseUrl,
  createDocument,
  generateCoverLetter,
  type Application,
  type ApplicationScrapePreview,
  type ApplicationSource,
  type ApplicationTag,
  type Company,
  type DocumentItem,
} from "@/lib/api";
import { APPLICATION_STAGES, type ApplicationStage } from "@/lib/application-stages";
import { formatStatus } from "@/lib/format";
import {
  DEFAULT_SALARY_CURRENCY,
  SALARY_PRESETS,
  convertCurrencyAmount,
  formatSalaryRange,
  presetToSalaryRange,
  salaryAmountFromPln,
  salaryAmountToPln,
  salaryPresetLabel,
  salaryRangeToPreset,
  type SalaryCurrency,
  type SalaryPresetId,
} from "@/lib/salary";
import { SENIORITY_LEVELS, type SeniorityLevel } from "@/lib/seniority-levels";

type ApplicationDialogProps = {
  applicationId?: number;
  onCreated?: () => void | Promise<void>;
  onSaved?: () => void | Promise<void>;
  triggerLabel?: string | null;
  triggerTitle?: string;
  triggerSize?: ButtonProps["size"];
  triggerVariant?: ButtonProps["variant"];
};

type ApplicationForm = {
  company_id: string;
  application_source_id: string;
  cv_document_id: string;
  position_url: string;
  company_name: string;
  source_name: string;
  position_title: string;
  position_description: string;
  location: string;
  remote_policy: string;
  seniority: SeniorityLevel | "";
  employment_type: string;
  salary_currency: SalaryCurrency;
  salary_preset: SalaryPresetId;
  salary_min: string;
  salary_max: string;
  status: ApplicationStage;
  rejection_reason: string;
  applied_at: string;
  notes: string;
  contact_url: string;
  contact_description: string;
  recruitment_description: string;
  cover_letter: string;
  tags: ApplicationTag[];
  raw_position_text: string;
  raw_position_source: string;
};

const LOCATION_OPTIONS = ["Remote", "Warsaw"] as const;
const WORK_FORMAT_OPTIONS = ["Remote", "Hybrid", "On-site"] as const;
const EMPLOYMENT_TYPE_OPTIONS = ["Full-time", "Freelance"] as const;

const emptyForm: ApplicationForm = {
  company_id: "",
  application_source_id: "",
  cv_document_id: "",
  position_url: "",
  company_name: "",
  source_name: "",
  position_title: "",
  position_description: "",
  location: "Remote",
  remote_policy: "Remote",
  seniority: "",
  employment_type: "Full-time",
  salary_currency: DEFAULT_SALARY_CURRENCY,
  salary_preset: "none",
  salary_min: "",
  salary_max: "",
  status: "sent_cv",
  rejection_reason: "",
  applied_at: todayInputValue(),
  contact_url: "",
  contact_description: "",
  recruitment_description: "",
  cover_letter: "",
  notes: "",
  tags: [],
  raw_position_text: "",
  raw_position_source: "",
};

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

function toIsoDate(value: string) {
  return new Date(`${value}T12:00:00`).toISOString();
}

function toDateInput(value: string) {
  return new Date(value).toISOString().slice(0, 10);
}

function buildNotes(form: ApplicationForm) {
  const sections = [
    form.position_description.trim()
      ? `Position description:\n${form.position_description.trim()}`
      : "",
    [
      form.location.trim() ? `Location: ${form.location.trim()}` : "",
      form.remote_policy.trim() ? `Work format: ${form.remote_policy.trim()}` : "",
      form.employment_type.trim() ? `Employment type: ${form.employment_type.trim()}` : "",
    ]
      .filter(Boolean)
      .join("\n"),
    form.notes.trim() ? `Notes:\n${form.notes.trim()}` : "",
  ].filter(Boolean);

  return sections.length > 0 ? sections.join("\n\n") : null;
}

function normalizeLocation(value: string | null, fallback: string) {
  const normalized = (value ?? "").trim().toLocaleLowerCase();
  if (!normalized) {
    return fallback;
  }
  if (normalized.includes("warsaw") || normalized.includes("warsaw")) {
    return "Warsaw";
  }
  if (normalized.includes("remote") || normalized.includes("remote")) {
    return "Remote";
  }
  return fallback;
}

function normalizeWorkFormat(value: string | null, fallback: string) {
  const normalized = (value ?? "").trim().toLocaleLowerCase();
  if (!normalized) {
    return fallback;
  }
  if (normalized.includes("hybrid") || normalized.includes("hybrid")) {
    return "Hybrid";
  }
  if (
    normalized.includes("onsite") ||
    normalized.includes("on-site") ||
    normalized.includes("office")
  ) {
    return "On-site";
  }
  if (normalized.includes("remote") || normalized.includes("remote")) {
    return "Remote";
  }
  return fallback;
}

function normalizeEmploymentType(value: string | null, fallback: string) {
  const normalized = (value ?? "").trim().toLocaleLowerCase();
  if (!normalized) {
    return fallback;
  }
  if (
    normalized.includes("freelance") ||
    normalized.includes("contract") ||
    normalized.includes("freelance")
  ) {
    return "Freelance";
  }
  if (normalized.includes("full") || normalized.includes("full")) {
    return "Full-time";
  }
  return fallback;
}

function applicationToForm(application: Application): ApplicationForm {
  const salaryPreset = salaryRangeToPreset(
    application.expected_salary_min_pln,
    application.expected_salary_max_pln,
  );

  return {
    company_id: String(application.company_id),
    application_source_id: application.application_source_id
      ? String(application.application_source_id)
      : "",
    cv_document_id: application.primary_document_id ? String(application.primary_document_id) : "",
    position_url: application.position_url ?? application.source_url ?? "",
    company_name: application.company_name,
    source_name: application.application_source_name ?? "",
    position_title: application.position_title,
    position_description: application.raw_position_text ?? "",
    location: "Remote",
    remote_policy: "Remote",
    seniority: application.seniority ?? "",
    employment_type: "Full-time",
    salary_currency: DEFAULT_SALARY_CURRENCY,
    salary_preset: salaryPreset,
    salary_min:
      salaryPreset === "custom" && application.expected_salary_min_pln !== null
        ? String(salaryAmountFromPln(application.expected_salary_min_pln, DEFAULT_SALARY_CURRENCY))
        : "",
    salary_max:
      salaryPreset === "custom" && application.expected_salary_max_pln !== null
        ? String(salaryAmountFromPln(application.expected_salary_max_pln, DEFAULT_SALARY_CURRENCY))
        : "",
    status: application.status,
    rejection_reason: application.rejection_reason ?? "",
    applied_at: toDateInput(application.applied_at),
    contact_url: application.contact_url ?? "",
    contact_description: application.contact_description ?? "",
    recruitment_description: application.recruitment_description ?? "",
    cover_letter: application.cover_letter ?? "",
    notes: application.notes ?? "",
    tags: application.tags,
    raw_position_text: application.raw_position_text ?? "",
    raw_position_source: application.raw_position_source ?? "",
  };
}

function numericInputToAmount(value: string) {
  const normalized = value.replace(",", ".").trim();
  if (!normalized) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function salaryFormRange(form: ApplicationForm) {
  if (form.salary_preset !== "custom") {
    return presetToSalaryRange(form.salary_preset);
  }

  const minAmount = numericInputToAmount(form.salary_min);
  const maxAmount = numericInputToAmount(form.salary_max);

  return {
    minPln: minAmount === null ? null : salaryAmountToPln(minAmount, form.salary_currency),
    maxPln: maxAmount === null ? null : salaryAmountToPln(maxAmount, form.salary_currency),
  };
}

function formatSalaryHelper(form: ApplicationForm) {
  const range = salaryFormRange(form);
  const monthly = formatSalaryRange(range.minPln, range.maxPln, "PLN");
  if (range.minPln === null && range.maxPln === null) {
    return `Stored in the database as ${monthly}.`;
  }

  const annualMin = range.minPln === null ? null : range.minPln * 12;
  const annualMax = range.maxPln === null ? null : range.maxPln * 12;
  const hourlyMin = range.minPln === null ? null : Math.round(range.minPln / 160);
  const hourlyMax = range.maxPln === null ? null : Math.round(range.maxPln / 160);

  return [
    `In DB: ${monthly} / mo.`,
    `Per year: ${formatSalaryRange(annualMin, annualMax, "PLN")}.`,
    `Per hour: ${formatSalaryRange(hourlyMin, hourlyMax, "PLN")}.`,
  ].join(" ");
}

function convertOptionalSalaryInput(
  value: string,
  fromCurrency: SalaryCurrency,
  toCurrency: SalaryCurrency,
) {
  const amount = numericInputToAmount(value);
  if (amount === null) {
    return "";
  }

  return String(Math.round(convertCurrencyAmount(amount, fromCurrency, toCurrency)));
}

export function ApplicationDialog({
  applicationId,
  onCreated,
  onSaved,
  triggerLabel,
  triggerTitle,
  triggerSize,
  triggerVariant,
}: ApplicationDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [applicationSources, setApplicationSources] = useState<ApplicationSource[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [form, setForm] = useState<ApplicationForm>(emptyForm);
  const [isTextDialogOpen, setIsTextDialogOpen] = useState(false);
  const [rawTextInput, setRawTextInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingCompany, setIsCreatingCompany] = useState(false);
  const [isCreatingSource, setIsCreatingSource] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [isParsingText, setIsParsingText] = useState(false);
  const [isGeneratingCoverLetter, setIsGeneratingCoverLetter] = useState(false);
  const [isSavingCoverLetter, setIsSavingCoverLetter] = useState(false);
  const [coverLetterFileName, setCoverLetterFileName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const cvDocuments = useMemo(
    () => documents.filter((document) => document.document_type === "cv"),
    [documents],
  );
  const selectableDocuments = cvDocuments.length > 0 ? cvDocuments : documents;
  const selectedCompanyExists = Boolean(form.company_id);
  const selectedSourceExists = Boolean(form.application_source_id);
  const isEditing = applicationId !== undefined;

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    let isMounted = true;

    async function loadFormData() {
      setIsLoading(true);
      setError(null);

      const [companiesResponse, sourcesResponse, documentsResponse, applicationResponse] =
        await Promise.all([
          fetch(`${apiBaseUrl}/api/companies`),
          fetch(`${apiBaseUrl}/api/application-sources`),
          fetch(`${apiBaseUrl}/api/documents`),
          isEditing
            ? fetch(`${apiBaseUrl}/api/applications/${applicationId}`)
            : Promise.resolve(null),
        ]);

      if (!isMounted) {
        return;
      }

      if (
        !companiesResponse.ok ||
        !sourcesResponse.ok ||
        !documentsResponse.ok ||
        (applicationResponse !== null && !applicationResponse.ok)
      ) {
        setError(
          isEditing
            ? "Failed to load application, companies, sources or documents"
            : "Failed to load companies, sources or documents",
        );
        setIsLoading(false);
        return;
      }

      const nextCompanies: Company[] = await companiesResponse.json();
      const nextSources: ApplicationSource[] = await sourcesResponse.json();
      const nextDocuments: DocumentItem[] = await documentsResponse.json();
      const nextCvDocuments = nextDocuments.filter((document) => document.document_type === "cv");
      const nextSelectableDocuments =
        nextCvDocuments.length > 0 ? nextCvDocuments : nextDocuments;

      const application: Application | null =
        applicationResponse === null ? null : await applicationResponse.json();

      setCompanies(nextCompanies);
      setApplicationSources(nextSources);
      setDocuments(nextDocuments);
      if (application) {
        setForm(applicationToForm(application));
      } else {
        setForm((current) => ({
          ...current,
          cv_document_id:
            current.cv_document_id ||
            (nextSelectableDocuments[0] ? nextSelectableDocuments[0].id : ""),
        }));
      }
      setIsLoading(false);
    }

    void loadFormData();

    return () => {
      isMounted = false;
    };
  }, [applicationId, isEditing, isOpen]);

  function closeDialog() {
    setIsOpen(false);
    setError(null);
    setWarnings([]);
    setIsCreatingCompany(false);
    setIsCreatingSource(false);
    setIsScraping(false);
    setIsParsingText(false);
    setIsGeneratingCoverLetter(false);
    setIsSavingCoverLetter(false);
    setCoverLetterFileName("");
    setIsTextDialogOpen(false);
    setRawTextInput("");
    setForm({ ...emptyForm, applied_at: todayInputValue() });
  }

  function applyScrapePreview(preview: ApplicationScrapePreview) {
    setForm((current) => ({
      ...current,
      company_id: preview.company_name ? "" : current.company_id,
      position_url: preview.source_url || current.position_url,
      company_name: preview.company_name ?? current.company_name,
      position_title: preview.position_title ?? current.position_title,
      position_description: preview.position_description ?? current.position_description,
      location: normalizeLocation(preview.location, current.location),
      remote_policy: normalizeWorkFormat(preview.remote_policy, current.remote_policy),
      seniority: preview.seniority ?? current.seniority,
      employment_type: normalizeEmploymentType(preview.employment_type, current.employment_type),
      contact_url: preview.contact_url ?? current.contact_url,
      contact_description: preview.contact_description ?? current.contact_description,
      recruitment_description: preview.recruitment_description ?? current.recruitment_description,
      tags: preview.tags,
      raw_position_text: preview.raw_text,
      raw_position_source: preview.raw_source,
    }));
    setWarnings(preview.warnings);
  }

  async function fillFromPositionUrl() {
    if (isScraping) {
      return;
    }

    const url = form.position_url.trim();
    setError(null);
    setWarnings([]);

    if (!url) {
      setError("Paste a link to the public job description");
      return;
    }

    setIsScraping(true);

    const response = await fetch(`${apiBaseUrl}/api/applications/scrape-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    setIsScraping(false);

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Failed to fill application from URL");
      return;
    }

    applyScrapePreview(await response.json());
  }

  async function parseRawText() {
    if (isParsingText) {
      return;
    }

    const text = rawTextInput.trim();
    setError(null);
    setWarnings([]);

    if (!text) {
      setError("Paste the exported job text");
      return;
    }

    setIsParsingText(true);

    const response = await fetch(`${apiBaseUrl}/api/applications/text-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        source_url: form.position_url.trim() || null,
      }),
    });

    setIsParsingText(false);

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Failed to parse job text");
      return;
    }

    applyScrapePreview(await response.json());
    setIsTextDialogOpen(false);
  }

  async function generateCoverLetterForForm() {
    if (isGeneratingCoverLetter) return;
    setError(null);
    setIsGeneratingCoverLetter(true);
    try {
      const content = await generateCoverLetter({
        position_title: form.position_title.trim(),
        company_name: form.company_name.trim(),
        notes: form.notes.trim() || null,
        raw_position_text: form.raw_position_text.trim() || null,
      });
      setForm((current) => ({ ...current, cover_letter: content }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate cover letter");
    } finally {
      setIsGeneratingCoverLetter(false);
    }
  }

  async function saveCoverLetterAsDocument() {
    if (isSavingCoverLetter) return;
    const rawName = coverLetterFileName.trim();
    if (!rawName) {
      setError("Enter a file name for the cover letter");
      return;
    }
    if (!form.cover_letter.trim()) {
      setError("Cover letter is empty — nothing to save");
      return;
    }
    const fileName = rawName.endsWith(".md") || rawName.endsWith(".docx") ? rawName : `${rawName}.md`;
    setError(null);
    setIsSavingCoverLetter(true);
    try {
      await createDocument({
        file_name: fileName,
        text: form.cover_letter,
        document_type: "cover_letter",
        company_id: form.company_id ? Number(form.company_id) : null,
      });
      const documentsResponse = await fetch(`${apiBaseUrl}/api/documents`);
      if (documentsResponse.ok) {
        const nextDocuments: DocumentItem[] = await documentsResponse.json();
        setDocuments(nextDocuments);
      }
      setCoverLetterFileName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save document");
    } finally {
      setIsSavingCoverLetter(false);
    }
  }

  async function createCompanyForCurrentApplication() {
    const name = form.company_name.trim();
    setError(null);

    if (!name) {
      setError("Enter a company name to create it for this application");
      return;
    }

    setIsCreatingCompany(true);

    const response = await fetch(`${apiBaseUrl}/api/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        website: null,
        notes: form.position_url.trim()
          ? `Created from application. Source: ${form.position_url.trim()}`
          : "Created from application.",
      }),
    });

    if (response.ok) {
      const createdCompany: Company = await response.json();
      setCompanies((current) =>
        [...current, createdCompany].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setForm((current) => ({ ...current, company_id: String(createdCompany.id) }));
      setIsCreatingCompany(false);
      return;
    }

    if (response.status === 409) {
      const companiesResponse = await fetch(`${apiBaseUrl}/api/companies`);
      if (companiesResponse.ok) {
        const nextCompanies: Company[] = await companiesResponse.json();
        const existingCompany = nextCompanies.find(
          (company) => company.name.toLocaleLowerCase() === name.toLocaleLowerCase(),
        );

        setCompanies(nextCompanies);
        if (existingCompany) {
          setForm((current) => ({ ...current, company_id: String(existingCompany.id) }));
          setIsCreatingCompany(false);
          return;
        }
      }
    }

    const body = await response.json().catch(() => null);
    setError(body?.detail ?? "Failed to create company");
    setIsCreatingCompany(false);
  }

  function updateCompanyName(value: string) {
    const existingCompany = companies.find(
      (company) => company.name.toLocaleLowerCase() === value.trim().toLocaleLowerCase(),
    );

    setForm((current) => ({
      ...current,
      company_name: value,
      company_id: existingCompany ? String(existingCompany.id) : "",
    }));
  }

  async function createSourceForCurrentApplication() {
    const name = form.source_name.trim();
    setError(null);

    if (!name) {
      setError("Enter a source name to create it for this application");
      return;
    }

    setIsCreatingSource(true);

    const response = await fetch(`${apiBaseUrl}/api/application-sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    if (response.ok) {
      const createdSource: ApplicationSource = await response.json();
      setApplicationSources((current) =>
        [...current, createdSource].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setForm((current) => ({
        ...current,
        application_source_id: String(createdSource.id),
      }));
      setIsCreatingSource(false);
      return;
    }

    if (response.status === 409) {
      const sourcesResponse = await fetch(`${apiBaseUrl}/api/application-sources`);
      if (sourcesResponse.ok) {
        const nextSources: ApplicationSource[] = await sourcesResponse.json();
        const existingSource = nextSources.find(
          (source) => source.name.toLocaleLowerCase() === name.toLocaleLowerCase(),
        );

        setApplicationSources(nextSources);
        if (existingSource) {
          setForm((current) => ({
            ...current,
            application_source_id: String(existingSource.id),
          }));
          setIsCreatingSource(false);
          return;
        }
      }
    }

    const body = await response.json().catch(() => null);
    setError(body?.detail ?? "Failed to create source");
    setIsCreatingSource(false);
  }

  function updateSourceName(value: string) {
    const existingSource = applicationSources.find(
      (source) => source.name.toLocaleLowerCase() === value.trim().toLocaleLowerCase(),
    );

    setForm((current) => ({
      ...current,
      source_name: value,
      application_source_id: existingSource ? String(existingSource.id) : "",
    }));
  }

  function updateSalaryCurrency(nextCurrency: SalaryCurrency) {
    setForm((current) => ({
      ...current,
      salary_currency: nextCurrency,
      salary_min:
        current.salary_preset === "custom"
          ? convertOptionalSalaryInput(current.salary_min, current.salary_currency, nextCurrency)
          : current.salary_min,
      salary_max:
        current.salary_preset === "custom"
          ? convertOptionalSalaryInput(current.salary_max, current.salary_currency, nextCurrency)
          : current.salary_max,
    }));
  }

  function updateSalaryPreset(nextPreset: SalaryPresetId) {
    setForm((current) => ({
      ...current,
      salary_preset: nextPreset,
      salary_min: nextPreset === "custom" ? current.salary_min : "",
      salary_max: nextPreset === "custom" ? current.salary_max : "",
    }));
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!form.company_id) {
      setError("Create at least one company first");
      return;
    }

    if (!isEditing && !form.cv_document_id) {
      setError("Select the CV that was sent for this position");
      return;
    }

    const salaryRange = salaryFormRange(form);
    if (
      salaryRange.minPln !== null &&
      salaryRange.maxPln !== null &&
      salaryRange.minPln > salaryRange.maxPln
    ) {
      setError("Minimum salary cannot be greater than maximum");
      return;
    }

    setIsSubmitting(true);

    const payload = {
      company_id: Number(form.company_id),
      application_source_id: form.application_source_id
        ? Number(form.application_source_id)
        : null,
      primary_document_id: form.cv_document_id ? Number(form.cv_document_id) : null,
      position_title: form.position_title.trim(),
      status: form.status,
      source_url: form.position_url.trim() || null,
      position_url: form.position_url.trim() || null,
      rejection_reason: form.rejection_reason.trim() || null,
      seniority: form.seniority || null,
      contact_url: form.contact_url.trim() || null,
      contact_description: form.contact_description.trim() || null,
      recruitment_description: form.recruitment_description.trim() || null,
      cover_letter: form.cover_letter.trim() || null,
      notes: buildNotes(form),
      applied_at: toIsoDate(form.applied_at),
      last_update_at: null,
      tags: form.tags,
      raw_position_text: form.raw_position_text || null,
      raw_position_source: form.raw_position_source || null,
      expected_salary_min_pln: salaryRange.minPln,
      expected_salary_max_pln: salaryRange.maxPln,
    };

    const response = await fetch(
      isEditing
        ? `${apiBaseUrl}/api/applications/${applicationId}`
        : `${apiBaseUrl}/api/applications`,
      {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );

    setIsSubmitting(false);

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Failed to save application");
      return;
    }

    closeDialog();

    if (onSaved) {
      await onSaved();
      return;
    }

    if (onCreated) {
      await onCreated();
      return;
    }

    window.location.reload();
  }

  return (
    <>
      <Button
        aria-label={
          triggerLabel === null
            ? (triggerTitle ?? (isEditing ? "Edit application" : "Add application"))
            : undefined
        }
        title={triggerTitle}
        type="button"
        size={triggerSize}
        variant={triggerVariant}
        onClick={() => setIsOpen(true)}
      >
        {isEditing ? <Pencil data-icon="inline-start" /> : <Plus data-icon="inline-start" />}
        {triggerLabel === null
          ? null
          : (triggerLabel ?? (isEditing ? "Edit" : "Add application"))}
      </Button>

      <AiLoader isLoading={isScraping || isParsingText || isGeneratingCoverLetter} />

      {isOpen ? (
        <div
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-background/80 px-4 py-8 backdrop-blur-sm"
          role="dialog"
        >
          <div className="w-full max-w-3xl rounded-lg border bg-card shadow-lg">
            <div className="flex items-start justify-between gap-4 border-b p-5">
              <div className="flex flex-col gap-1">
                <h2 className="text-xl font-semibold tracking-normal">
                  {isEditing ? "Edit application" : "Add application"}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {isEditing
                    ? "Edit the fields and save updates for this application."
                    : "Manual entry for now; scraping will be added in the next step."}
                </p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={closeDialog}>
                <X data-icon="inline-start" />
                Close
              </Button>
            </div>

            <form className="flex flex-col gap-5 p-5" onSubmit={submitForm}>
              <input name="position_url" type="hidden" value={form.position_url.trim()} />
              {error ? (
                <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
                  {error}
                </div>
              ) : null}

              <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Link to public job description
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    placeholder="https://..."
                    type="url"
                    value={form.position_url}
                    onChange={(event) => setForm({ ...form, position_url: event.target.value })}
                  />
                </label>
                <div className="flex items-end">
                  <Button
                    aria-busy={isScraping}
                    type="button"
                    variant="outline"
                    onClick={() => void fillFromPositionUrl()}
                  >
                    <WandSparkles data-icon="inline-start" />
                    {isScraping ? "Filling..." : "Fill"}
                  </Button>
                </div>
                <div className="flex items-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsTextDialogOpen(true)}
                  >
                    <Code2 data-icon="inline-start" />
                    Load page text
                  </Button>
                </div>
              </div>

              {warnings.length > 0 ? (
                <div className="flex flex-col gap-1 rounded-md border bg-muted p-3 text-sm text-muted-foreground">
                  {warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </div>
              ) : null}

              <div className="grid gap-4 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium">
                    Company
                  </label>
                  <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                    <SearchableSelect
                      disabled={isLoading}
                      options={companies.map((company) => ({
                        value: String(company.id),
                        label: company.name,
                      }))}
                      placeholder="Company name"
                      value={form.company_id || null}
                      onChange={(val) => {
                        const company = companies.find((c) => String(c.id) === val);
                        setForm((current) => ({
                          ...current,
                          company_id: val ? String(val) : "",
                          company_name: company ? company.name : current.company_name,
                        }));
                      }}
                      onSearchChange={(q) => {
                        if (q) updateCompanyName(q);
                      }}
                    />
                    <Button
                      className="h-10 min-w-14 bg-green-600 px-5 text-lg font-semibold text-white shadow-sm hover:bg-green-700"
                      disabled={selectedCompanyExists || isCreatingCompany || isLoading}
                      title="Create company from entered name and select it"
                      type="button"
                      onClick={() => void createCompanyForCurrentApplication()}
                    >
                      {isCreatingCompany ? "..." : "+"}
                    </Button>
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium">
                    Source
                  </label>
                  <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                    <SearchableSelect
                      disabled={isLoading}
                      options={applicationSources.map((source) => ({
                        value: String(source.id),
                        label: source.name,
                      }))}
                      placeholder="LinkedIn, Djinni, referral..."
                      value={form.application_source_id || null}
                      onChange={(val) => {
                        const source = applicationSources.find((s) => String(s.id) === val);
                        setForm((current) => ({
                          ...current,
                          application_source_id: val ? String(val) : "",
                          source_name: source ? source.name : current.source_name,
                        }));
                      }}
                      onSearchChange={(q) => {
                        if (q) updateSourceName(q);
                      }}
                    />
                    <Button
                      className="h-10 min-w-14 bg-green-600 px-5 text-lg font-semibold text-white shadow-sm hover:bg-green-700"
                      disabled={selectedSourceExists || isCreatingSource || isLoading}
                      title="Create source from entered name and select it"
                      type="button"
                      onClick={() => void createSourceForCurrentApplication()}
                    >
                      {isCreatingSource ? "..." : "+"}
                    </Button>
                  </div>
                </div>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Position name
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    required
                    value={form.position_title}
                    onChange={(event) =>
                      setForm({ ...form, position_title: event.target.value })
                    }
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  CV submitted for the position
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    disabled={isLoading || selectableDocuments.length === 0}
                    required={!isEditing}
                    value={form.cv_document_id}
                    onChange={(event) =>
                      setForm({ ...form, cv_document_id: event.target.value })
                    }
                  >
                    {selectableDocuments.map((document) => (
                      <option key={document.id} value={document.id}>
                        {document.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Status
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.status}
                    onChange={(event) =>
                      setForm({ ...form, status: event.target.value as ApplicationStage })
                    }
                  >
                    {APPLICATION_STAGES.map((status) => (
                      <option key={status} value={status}>
                        {formatStatus(status)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Application date
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    required
                    type="date"
                    value={form.applied_at}
                    onChange={(event) => setForm({ ...form, applied_at: event.target.value })}
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Location
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.location}
                    onChange={(event) => setForm({ ...form, location: event.target.value })}
                  >
                    {LOCATION_OPTIONS.map((location) => (
                      <option key={location} value={location}>
                        {location}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Work format
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.remote_policy}
                    onChange={(event) => setForm({ ...form, remote_policy: event.target.value })}
                  >
                    {WORK_FORMAT_OPTIONS.map((format) => (
                      <option key={format} value={format}>
                        {format}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Seniority
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.seniority}
                    onChange={(event) =>
                      setForm({ ...form, seniority: event.target.value as SeniorityLevel | "" })
                    }
                  >
                    <option value="">Not selected</option>
                    {SENIORITY_LEVELS.map((seniority) => (
                      <option key={seniority} value={seniority}>
                        {seniority}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Employment type
                  <select
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    value={form.employment_type}
                    onChange={(event) =>
                      setForm({ ...form, employment_type: event.target.value })
                    }
                  >
                    {EMPLOYMENT_TYPE_OPTIONS.map((employmentType) => (
                      <option key={employmentType} value={employmentType}>
                        {employmentType}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium">
                  Expected salary
                  <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_8rem]">
                    <select
                      className="h-10 rounded-md border bg-background px-3 text-sm"
                      value={form.salary_preset}
                      onChange={(event) => updateSalaryPreset(event.target.value as SalaryPresetId)}
                    >
                      <option value="none">{salaryPresetLabel("none", form.salary_currency)}</option>
                      {SALARY_PRESETS.map((preset) => (
                        <option key={preset.id} value={preset.id}>
                          {salaryPresetLabel(preset.id, form.salary_currency)}
                        </option>
                      ))}
                      <option value="custom">
                        {salaryPresetLabel("custom", form.salary_currency)}
                      </option>
                    </select>
                    <select
                      className="h-10 rounded-md border bg-background px-3 text-sm"
                      value={form.salary_currency}
                      onChange={(event) =>
                        updateSalaryCurrency(event.target.value as SalaryCurrency)
                      }
                    >
                      <option value="USD">USD</option>
                      <option value="PLN">PLN</option>
                    </select>
                  </div>
                  {form.salary_preset === "custom" ? (
                    <div className="grid gap-2 sm:grid-cols-2">
                      <input
                        className="h-10 rounded-md border bg-background px-3 text-sm"
                        inputMode="numeric"
                        min="0"
                        placeholder={`From, ${form.salary_currency}`}
                        type="number"
                        value={form.salary_min}
                        onChange={(event) =>
                          setForm({ ...form, salary_min: event.target.value })
                        }
                      />
                      <input
                        className="h-10 rounded-md border bg-background px-3 text-sm"
                        inputMode="numeric"
                        min="0"
                        placeholder={`To, ${form.salary_currency}`}
                        type="number"
                        value={form.salary_max}
                        onChange={(event) =>
                          setForm({ ...form, salary_max: event.target.value })
                        }
                      />
                    </div>
                  ) : null}
                  <span className="text-xs font-normal text-muted-foreground">
                    {formatSalaryHelper(form)}
                  </span>
                </label>

                <div className="flex items-end">
                  <p className="text-sm text-muted-foreground">
                    {selectedCompanyExists
                      ? "Company found in the database and will be linked to the application."
                      : "If the company is not in the database, click + after verifying the name."}
                  </p>
                </div>
              </div>

              {selectableDocuments.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No CV files in the documents folder. Add a CV to documents to save the application.
                </p>
              ) : null}

              <label className="flex flex-col gap-2 text-sm font-medium">
                Position description text
                <textarea
                  className="min-h-36 rounded-md border bg-background px-3 py-2 text-sm"
                  value={form.position_description}
                  onChange={(event) =>
                    setForm({ ...form, position_description: event.target.value })
                  }
                />
              </label>

              {form.tags.length > 0 ? (
                <div className="flex flex-col gap-2">
                  <p className="text-sm font-medium">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {form.tags.map((tag) => (
                      <span
                        className="rounded-md border bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground"
                        key={`${tag.kind}-${tag.name}`}
                        title={tag.kind}
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              <label className="flex flex-col gap-2 text-sm font-medium">
                Notes
                <textarea
                  className="min-h-24 rounded-md border bg-background px-3 py-2 text-sm"
                  value={form.notes}
                  onChange={(event) => setForm({ ...form, notes: event.target.value })}
                />
              </label>

              <div className="flex flex-col gap-3 rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Cover letter</p>
                  <Button
                    aria-busy={isGeneratingCoverLetter}
                    disabled={isGeneratingCoverLetter}
                    size="sm"
                    type="button"
                    variant="outline"
                    onClick={() => void generateCoverLetterForForm()}
                  >
                    <WandSparkles data-icon="inline-start" />
                    {isGeneratingCoverLetter ? "Generating..." : "Generate"}
                  </Button>
                </div>
                <textarea
                  className="min-h-48 rounded-md border bg-background px-3 py-2 text-sm"
                  placeholder="Paste or generate a cover letter..."
                  value={form.cover_letter}
                  onChange={(event) => setForm({ ...form, cover_letter: event.target.value })}
                />
                <div className="flex items-end gap-2">
                  <label className="flex flex-1 flex-col gap-1 text-sm font-medium">
                    File name
                    <input
                      className="h-9 rounded-md border bg-background px-3 text-sm"
                      placeholder="cover-letter (no extension)"
                      value={coverLetterFileName}
                      onChange={(event) => setCoverLetterFileName(event.target.value)}
                    />
                  </label>
                  <Button
                    aria-busy={isSavingCoverLetter}
                    disabled={isSavingCoverLetter || !coverLetterFileName.trim() || !form.cover_letter.trim()}
                    size="sm"
                    type="button"
                    variant="outline"
                    onClick={() => void saveCoverLetterAsDocument()}
                  >
                    <Save data-icon="inline-start" />
                    {isSavingCoverLetter ? "Saving..." : "Save to document"}
                  </Button>
                </div>
              </div>

              <div className="flex flex-col gap-3">
                <p className="text-sm font-medium">Contact</p>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Contact link
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    placeholder="https://..."
                    type="url"
                    value={form.contact_url}
                    onChange={(event) => setForm({ ...form, contact_url: event.target.value })}
                  />
                </label>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Contact description
                  <textarea
                    className="min-h-20 rounded-md border bg-background px-3 py-2 text-sm"
                    placeholder="Name, title, notes..."
                    value={form.contact_description}
                    onChange={(event) =>
                      setForm({ ...form, contact_description: event.target.value })
                    }
                  />
                </label>
              </div>

              <div className="flex flex-col gap-4 rounded-lg border p-4">
                <p className="text-sm font-semibold">Recruitment process</p>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Process description
                  <textarea
                    className="min-h-20 rounded-md border bg-background px-3 py-2 text-sm"
                    placeholder="Stages, interview format, timeline..."
                    value={form.recruitment_description}
                    onChange={(event) =>
                      setForm({ ...form, recruitment_description: event.target.value })
                    }
                  />
                </label>
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={closeDialog}>
                  Cancel
                </Button>
                <Button
                  disabled={
                    isSubmitting || isLoading || (!isEditing && selectableDocuments.length === 0)
                  }
                >
                  {isEditing ? (
                    <Pencil data-icon="inline-start" />
                  ) : (
                    <Plus data-icon="inline-start" />
                  )}
                  {isSubmitting
                    ? "Saving..."
                    : isEditing
                      ? "Save changes"
                      : "Save application"}
                </Button>
              </div>
            </form>
          </div>

          {isTextDialogOpen ? (
            <div
              aria-modal="true"
              className="fixed inset-0 flex items-start justify-center overflow-y-auto bg-background/80 px-4 py-10 backdrop-blur-sm"
              role="dialog"
            >
              <div className="w-full max-w-4xl rounded-lg border bg-card shadow-lg">
                <div className="flex items-start justify-between gap-4 border-b p-5">
                  <div className="flex flex-col gap-1">
                    <h3 className="text-lg font-semibold tracking-normal">
                      Exported job text
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Paste the text content of the page. It will be used for field and tag extraction.
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsTextDialogOpen(false)}
                  >
                    <X data-icon="inline-start" />
                    Close
                  </Button>
                </div>
                <div className="flex flex-col gap-4 p-5">
                  <textarea
                    className="min-h-96 rounded-md border bg-background px-3 py-2 text-sm"
                    placeholder="Paste job text here..."
                    value={rawTextInput}
                    onChange={(event) => setRawTextInput(event.target.value)}
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsTextDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      aria-busy={isParsingText}
                      type="button"
                      onClick={() => void parseRawText()}
                    >
                      <WandSparkles data-icon="inline-start" />
                      {isParsingText ? "Parsing..." : "Save and parse"}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

    </>
  );
}
