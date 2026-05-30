import type { ApplicationStage } from "@/lib/application-stages";
import type { SeniorityLevel } from "@/lib/seniority-levels";

export type DashboardStats = {
  applications_total: number;
  updates_total: number;
  applications_today: number;
  updates_today: number;
  applications_last_30_days: number;
  updates_last_30_days: number;
};

export type SeniorityCount = {
  seniority: SeniorityLevel | null;
  count: number;
};

export type RecentCompany = {
  company_id: number;
  latest_application_id: number;
  company_name: string;
  applications_count: number;
  latest_position: string;
  latest_status: ApplicationStage;
  latest_added_at: string;
  latest_applied_at: string;
};

export type DocumentItem = {
  id: string;
  name: string;
  path: string;
  size_bytes: number;
  modified_at: string;
  document_type: string;
  company_id: number | null;
  company_name: string | null;
};

export type DocumentPreview = {
  lines: string[];
  line_count: number;
  truncated: boolean;
  unsupported_reason: string | null;
};

export type TimelinePoint = {
  date: string;
  applications: number;
  updates: number;
};

export type DashboardResponse = {
  stats: DashboardStats;
  seniority_all_time: SeniorityCount[];
  seniority_today: SeniorityCount[];
  recent_companies: RecentCompany[];
  documents: DocumentItem[];
  storage_dir: string;
  timeline: TimelinePoint[];
};

export type PageResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  sort: string;
  direction: "asc" | "desc";
};

export type PageQuery = {
  page: number;
  pageSize: number;
  sort: string;
  direction: "asc" | "desc";
};

export type ApplicationsPageQuery = PageQuery & {
  includeClosed?: boolean;
  q?: string;
};

// Server-side (SSR) needs absolute URL; client-side uses relative path so Caddy can proxy it.
const _envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
export const apiBaseUrl =
  _envUrl || (typeof window === "undefined" ? "http://127.0.0.1:8000" : "");

function pageSearchParams(query: PageQuery) {
  const params = new URLSearchParams({
    direction: query.direction,
    page: String(query.page),
    page_size: String(query.pageSize),
    sort: query.sort,
  });
  return params.toString();
}

function applicationsPageSearchParams(query: ApplicationsPageQuery) {
  const params = new URLSearchParams(pageSearchParams(query));
  if (query.includeClosed) {
    params.set("include_closed", "true");
  }
  if (query.q?.trim()) {
    params.set("q", query.q.trim());
  }
  return params.toString();
}

export async function getDashboard(): Promise<DashboardResponse> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Dashboard API failed with ${response.status}`);
  }

  return response.json();
}

export async function getDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${apiBaseUrl}/api/documents`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Documents API failed with ${response.status}`);
  }

  return response.json();
}

export async function getDocumentsPage(query: PageQuery): Promise<PageResponse<DocumentItem>> {
  const response = await fetch(`${apiBaseUrl}/api/documents/page?${pageSearchParams(query)}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Documents page API failed with ${response.status}`);
  }

  return response.json();
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const response = await fetch(`${apiBaseUrl}/api/documents/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Document API failed with ${response.status}`);
  }

  return response.json();
}

export async function getDocumentPreview(id: string): Promise<DocumentPreview> {
  const response = await fetch(`${apiBaseUrl}/api/documents/${id}/preview`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Document preview API failed with ${response.status}`);
  }

  return response.json();
}

export async function createDocument(payload: {
  file_name: string;
  text: string;
  document_type: "cv" | "cover_letter" | "other";
  company_id: number | null;
}): Promise<DocumentItem> {
  const response = await fetch(`${apiBaseUrl}/api/documents`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Document create failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/documents/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Document delete API failed with ${response.status}`);
  }
}

export type Company = {
  id: number;
  name: string;
  website: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  applications_count: number;
};

export async function getCompaniesPage(query: PageQuery): Promise<PageResponse<Company>> {
  const response = await fetch(`${apiBaseUrl}/api/companies/page?${pageSearchParams(query)}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Companies page API failed with ${response.status}`);
  }

  return response.json();
}

export type ApplicationSource = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  applications_count: number;
};

export type Application = {
  id: number;
  company_id: number;
  company_name: string;
  application_source_id: number | null;
  application_source_name: string | null;
  primary_document_id: number | null;
  position_title: string;
  status: ApplicationStage;
  source_url: string | null;
  position_url: string | null;
  rejection_reason: string | null;
  seniority: SeniorityLevel | null;
  contact_url: string | null;
  contact_description: string | null;
  recruitment_description: string | null;
  cover_letter: string | null;
  notes: string | null;
  raw_position_text: string | null;
  raw_position_source: string | null;
  expected_salary_min_pln: number | null;
  expected_salary_max_pln: number | null;
  applied_at: string;
  last_update_at: string | null;
  created_at: string;
  updated_at: string;
  tags: ApplicationTag[];
};

export async function getApplicationsPage(
  query: ApplicationsPageQuery,
): Promise<PageResponse<Application>> {
  const response = await fetch(
    `${apiBaseUrl}/api/applications/page?${applicationsPageSearchParams(query)}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(`Applications page API failed with ${response.status}`);
  }

  return response.json();
}

export type ApplicationTag = {
  id?: number;
  name: string;
  kind: string;
  confidence: number | null;
  source: string | null;
};

export type ApplicationScrapePreview = {
  source_url: string;
  company_name: string | null;
  position_title: string | null;
  position_description: string | null;
  location: string | null;
  remote_policy: string | null;
  seniority: SeniorityLevel | null;
  employment_type: string | null;
  salary: string | null;
  contact_url: string | null;
  contact_description: string | null;
  recruitment_description: string | null;
  tags: ApplicationTag[];
  raw_text: string;
  raw_source: string;
  warnings: string[];
};

export type GmailStatus = {
  connected: boolean;
  email_address: string | null;
  last_sync_at: string | null;
  messages_count: number;
  token_file_exists: boolean;
  client_secret_file_exists: boolean;
  sync_query: string;
};

export type GmailMessage = {
  id: number;
  gmail_id: string;
  thread_id: string;
  sender: string | null;
  recipients: string | null;
  subject: string | null;
  snippet: string | null;
  internal_date: string | null;
  received_at: string | null;
};

export type CodexStatus = {
  command: string[];
  cwd: string;
  timeout_seconds: number;
};

export type CodexAskResponse = {
  answer: string;
  stderr: string | null;
  context_source: string;
  warnings: string[];
};

export type FeatureMemory = {
  id: number;
  text: string;
  page_url: string;
  page_title: string | null;
  screenshot_data_url: string;
  created_at: string;
  closed_at: string | null;
};

export async function getGmailStatus(): Promise<GmailStatus> {
  const response = await fetch(`${apiBaseUrl}/api/gmail/status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Gmail status API failed with ${response.status}`);
  }

  return response.json();
}

export async function getGmailMessages(): Promise<GmailMessage[]> {
  const response = await fetch(`${apiBaseUrl}/api/gmail/messages`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Gmail messages API failed with ${response.status}`);
  }

  return response.json();
}

export async function getGmailMessagesPage(
  query: PageQuery,
): Promise<PageResponse<GmailMessage>> {
  const response = await fetch(`${apiBaseUrl}/api/gmail/messages/page?${pageSearchParams(query)}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Gmail messages page API failed with ${response.status}`);
  }

  return response.json();
}

export async function deleteGmailMessage(id: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/gmail/messages/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Gmail message delete failed with ${response.status}${detail}`);
  }
}

export async function getCodexStatus(): Promise<CodexStatus> {
  const response = await fetch(`${apiBaseUrl}/api/codex/status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Codex status API failed with ${response.status}`);
  }

  return response.json();
}

export async function askCodex(
  question: string,
  mode: "text" | "url",
  context?: string,
  contextUrl?: string,
): Promise<CodexAskResponse> {
  const response = await fetch(`${apiBaseUrl}/api/codex/ask`, {
    body: JSON.stringify({
      question,
      mode,
      context: context || null,
      context_url: contextUrl || null,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail ? `: ${payload.detail}` : "";
    throw new Error(`Codex bridge failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function createFeatureMemory(payload: {
  text: string;
  page_url: string;
  page_title: string | null;
  screenshot_data_url: string;
}): Promise<FeatureMemory> {
  const response = await fetch(`${apiBaseUrl}/api/feature-memories`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Feature memory create failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function getFeatureMemories(): Promise<FeatureMemory[]> {
  const response = await fetch(`${apiBaseUrl}/api/feature-memories`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Feature memories API failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function getFeatureMemoriesPage(
  query: PageQuery,
): Promise<PageResponse<FeatureMemory>> {
  const response = await fetch(
    `${apiBaseUrl}/api/feature-memories/page?${pageSearchParams(query)}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Feature memories page API failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function getRecentCompaniesPage(
  query: PageQuery,
): Promise<PageResponse<RecentCompany>> {
  const response = await fetch(
    `${apiBaseUrl}/api/dashboard/recent-companies/page?${pageSearchParams(query)}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(`Recent companies page API failed with ${response.status}`);
  }

  return response.json();
}

export async function updateFeatureMemory(
  id: number,
  payload: { text: string; page_title: string | null },
): Promise<FeatureMemory> {
  const response = await fetch(`${apiBaseUrl}/api/feature-memories/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Feature memory update failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function closeFeatureMemory(id: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/feature-memories/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Feature memory close failed with ${response.status}${detail}`);
  }
}

export type Prompt = {
  id: number;
  name: string;
  description: string | null;
  content: string;
  created_at: string;
  updated_at: string;
};

export async function getPrompts(): Promise<Prompt[]> {
  const response = await fetch(`${apiBaseUrl}/api/prompts`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Prompts API failed with ${response.status}`);
  }

  return response.json();
}

export async function getPrompt(id: number): Promise<Prompt> {
  const response = await fetch(`${apiBaseUrl}/api/prompts/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Prompt API failed with ${response.status}`);
  }

  return response.json();
}

export async function createPrompt(data: {
  name: string;
  description: string | null;
  content: string;
}): Promise<Prompt> {
  const response = await fetch(`${apiBaseUrl}/api/prompts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Prompt create failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function updatePrompt(
  id: number,
  data: { description: string | null; content: string },
): Promise<Prompt> {
  const response = await fetch(`${apiBaseUrl}/api/prompts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Prompt update failed with ${response.status}${detail}`);
  }

  return response.json();
}

export async function deletePrompt(id: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/prompts/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ? `: ${body.detail}` : "";
    throw new Error(`Prompt delete failed with ${response.status}${detail}`);
  }
}

export type CoverLetterRequest = {
  position_title: string;
  company_name: string;
  notes?: string | null;
  raw_position_text?: string | null;
};

export async function generateCoverLetter(payload: CoverLetterRequest): Promise<string> {
  const response = await fetch(`${apiBaseUrl}/api/codex/cover-letter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Cover letter generation failed with ${response.status}`);
  }

  const data = await response.json();
  return data.content;
}
