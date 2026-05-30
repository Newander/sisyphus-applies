"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Ban, Plus, Search, Trash2 } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { ApplicationDialog } from "@/components/application-dialog";
import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiBaseUrl, getApplicationsPage, type Application } from "@/lib/api";
import { formatDate, formatStatus } from "@/lib/format";
import { formatSalaryRange } from "@/lib/salary";

const DEFAULT_REJECTION_REASONS = [
  "Experience did not match",
  "Salary did not match",
  "Format did not match",
  "Position closed",
  "No response after interview",
  "Chose another option",
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [totalApplications, setTotalApplications] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeClosed, setIncludeClosed] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearchQuery(searchInput), 350);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchInput]);

  const columns = useMemo<DataTableColumn<Application>[]>(
    () => [
      {
        id: "applied_at",
        header: "Date",
        accessor: "applied_at",
        className: "text-muted-foreground",
        sortValue: (application) => new Date(application.applied_at),
        cell: (application) => formatDate(application.applied_at),
      },
      {
        id: "company_name",
        header: "Company",
        accessor: "company_name",
        className: "font-medium",
      },
      {
        id: "application_source_name",
        header: "Source",
        className: "text-muted-foreground",
        sortValue: (application) => application.application_source_name ?? "",
        cell: (application) => application.application_source_name ?? "-",
      },
      {
        id: "position_title",
        header: "Position",
        accessor: "position_title",
      },
      {
        id: "expected_salary_min_pln",
        header: "Salary",
        className: "text-muted-foreground",
        sortValue: (application) => application.expected_salary_min_pln ?? 0,
        cell: (application) =>
          formatSalaryRange(
            application.expected_salary_min_pln,
            application.expected_salary_max_pln,
          ),
      },
      {
        id: "status",
        header: "Status",
        sortValue: (application) => formatStatus(application.status),
        cell: (application) => (
          <Badge variant="secondary">{formatStatus(application.status)}</Badge>
        ),
      },
    ],
    [],
  );

  const loadApplications = useCallback(
    async (query: DataTableQuery) => {
      setIsLoading(true);
      setError(null);

      try {
        const page = await getApplicationsPage({
          direction: query.sort?.direction ?? "desc",
          includeClosed,
          page: query.page,
          pageSize: query.pageSize,
          sort: query.sort?.columnId ?? "applied_at",
          q: searchQuery || undefined,
        });
        setApplications(page.items);
        setTotalApplications(page.total);
      } catch {
        setError("Failed to load application history");
      } finally {
        setIsLoading(false);
      }
    },
    [includeClosed, searchQuery],
  );

  const reloadFirstPage = useCallback(
    () =>
      loadApplications({
        page: 1,
        pageSize: 10,
        sort: { columnId: "applied_at", direction: "desc" },
      }),
    [loadApplications],
  );

  async function deleteApplication(application: Application) {
    if (!window.confirm(`Delete application for ${application.position_title}?`)) {
      return;
    }

    const response = await fetch(`${apiBaseUrl}/api/applications/${application.id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Failed to delete application");
      return;
    }

    setApplications((current) => current.filter((item) => item.id !== application.id));
    setTotalApplications((current) => Math.max(0, current - 1));
  }

  function updateApplication(application: Application) {
    setApplications((current) =>
      current.map((item) => (item.id === application.id ? application : item)),
    );
  }

  const rejectionReasons = useMemo(
    () =>
      Array.from(
        new Set(
          [
            ...DEFAULT_REJECTION_REASONS,
            ...applications
              .map((application) => application.rejection_reason?.trim())
              .filter((reason): reason is string => Boolean(reason)),
          ].sort((first, second) => first.localeCompare(second, "ru")),
        ),
      ),
    [applications],
  );

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="applications" />
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium text-muted-foreground">Submission history</p>
              <h1 className="text-3xl font-semibold tracking-normal">Applications</h1>
            </div>
            <ApplicationDialog onCreated={reloadFirstPage} />
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="flex flex-col gap-1">
                <CardTitle>Application history</CardTitle>
                <CardDescription>
                  {totalApplications} {includeClosed ? "applications" : "open applications"} in
                  the local database.
                </CardDescription>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                  <input
                    className="h-9 rounded-md border bg-background pl-8 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    placeholder="Search by position, company..."
                    type="search"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                  />
                </div>
                <label className="flex items-center gap-2 text-sm font-medium">
                  <input
                    checked={includeClosed}
                    className="size-4"
                    type="checkbox"
                    onChange={(event) => setIncludeClosed(event.target.checked)}
                  />
                  Show closed
                </label>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <DataTable
              key={`${includeClosed ? "with-closed" : "without-closed"}-${searchQuery}`}
              columns={columns}
              data={applications}
              emptyMessage="No applications yet."
              initialSort={{ columnId: "applied_at", direction: "desc" }}
              isLoading={isLoading}
              onQueryChange={loadApplications}
              rowKey={(application) => application.id}
              totalItems={totalApplications}
              renderActions={(application) => (
                <>
                  <ApplicationDialog
                    applicationId={application.id}
                    onSaved={reloadFirstPage}
                    triggerLabel={null}
                    triggerSize="icon"
                    triggerTitle="Edit"
                    triggerVariant="outline"
                  />
                  <RejectionDialog
                    application={application}
                    reasons={rejectionReasons}
                    onSaved={includeClosed ? updateApplication : reloadFirstPage}
                  />
                  <Button
                    aria-label="Delete"
                    title="Delete"
                    type="button"
                    variant="destructive"
                    size="icon"
                    onClick={() => void deleteApplication(application)}
                  >
                    <Trash2 />
                  </Button>
                </>
              )}
            />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

type RejectionDialogProps = {
  application: Application;
  reasons: string[];
  onSaved: (application: Application) => void;
};

function RejectionDialog({ application, reasons, onSaved }: RejectionDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedReason, setSelectedReason] = useState(application.rejection_reason ?? "");
  const [customReason, setCustomReason] = useState("");
  const [localReasons, setLocalReasons] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allReasons = useMemo(
    () =>
      Array.from(
        new Set(
          [...reasons, ...localReasons]
            .map((reason) => reason.trim())
            .filter((reason) => reason.length > 0)
            .sort((first, second) => first.localeCompare(second, "en")),
        ),
      ),
    [localReasons, reasons],
  );

  function openDialog() {
    setSelectedReason(application.rejection_reason ?? "");
    setCustomReason("");
    setError(null);
    setIsOpen(true);
  }

  function addCustomReason() {
    const reason = customReason.trim();
    if (!reason) {
      setError("Enter a rejection reason");
      return;
    }

    setLocalReasons((current) =>
      current.some((item) => item.toLocaleLowerCase() === reason.toLocaleLowerCase())
        ? current
        : [...current, reason],
    );
    setSelectedReason(reason);
    setCustomReason("");
    setError(null);
  }

  async function submitRejection(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const reason = selectedReason.trim();
    if (!reason) {
      setError("Select or add a rejection reason");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const response = await fetch(`${apiBaseUrl}/api/applications/${application.id}/rejection`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rejection_reason: reason }),
    });

    setIsSubmitting(false);

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Failed to save rejection reason");
      return;
    }

    onSaved(await response.json());
    setIsOpen(false);
  }

  return (
    <>
      <Button
        aria-label="Reject"
        title="Reject"
        type="button"
        variant="outline"
        size="icon"
        onClick={openDialog}
      >
        <Ban />
      </Button>

      {isOpen ? (
        <div
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-start justify-center bg-background/80 px-4 py-10 backdrop-blur-sm"
          role="dialog"
        >
          <form
            className="flex w-full max-w-md flex-col gap-4 rounded-lg border bg-card p-5 shadow-lg"
            onSubmit={submitRejection}
          >
            <div className="flex flex-col gap-1">
              <h2 className="text-lg font-semibold tracking-normal">Rejection reason</h2>
              <p className="text-sm text-muted-foreground">{application.position_title}</p>
            </div>

            {error ? (
              <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            <label className="flex flex-col gap-2 text-sm font-medium">
              Reason
              <select
                className="h-10 rounded-md border bg-background px-3 text-sm"
                value={selectedReason}
                onChange={(event) => setSelectedReason(event.target.value)}
              >
                <option value="">Select a reason</option>
                {allReasons.map((reason) => (
                  <option key={reason} value={reason}>
                    {reason}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium">
              New value
              <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <input
                  className="h-10 rounded-md border bg-background px-3 text-sm"
                  placeholder="E.g.: tech stack did not match"
                  value={customReason}
                  onChange={(event) => setCustomReason(event.target.value)}
                />
                <Button
                  aria-label="Add reason"
                  title="Add reason"
                  type="button"
                  variant="outline"
                  onClick={addCustomReason}
                >
                  <Plus data-icon="inline-start" />
                </Button>
              </div>
            </label>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button disabled={isSubmitting}>
                {isSubmitting ? "Saving..." : "Save"}
              </Button>
            </div>
          </form>
        </div>
      ) : null}
    </>
  );
}
