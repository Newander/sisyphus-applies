import { BriefcaseBusiness, Building2, FileText, Inbox } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { ApplicationDialog } from "@/components/application-dialog";
import { ApplicationsTimelineChart } from "@/components/applications-timeline-chart";
import { CreateDocumentDialog } from "@/components/create-document-dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  apiBaseUrl,
  getDashboard,
  getDocumentsPage,
  getRecentCompaniesPage,
  type SeniorityCount,
} from "@/lib/api";
import { DashboardDocumentsTable, RecentCompaniesTable } from "./dashboard-tables";

function MetricCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: number;
  description: string;
  icon: typeof BriefcaseBusiness;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold">{value}</div>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function SeniorityStatsCard({
  title,
  description,
  rows,
  total,
}: {
  title: string;
  description: string;
  rows: SeniorityCount[];
  total: number;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1.5">
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="rounded-md bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
            {total}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="rounded-md bg-muted px-3 py-6 text-center text-sm text-muted-foreground">
            No applications for this period.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Seniority</TableHead>
                <TableHead className="w-24 text-right">Applications</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.seniority ?? "empty-seniority"}>
                  <TableCell className="font-medium">
                    {row.seniority ?? "Not specified"}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="rounded-md bg-muted px-2 py-1 font-semibold">
                      {row.count}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

export default async function DashboardPage() {
  const data = await Promise.all([
    getDashboard(),
    getRecentCompaniesPage({
      direction: "desc",
      page: 1,
      pageSize: 5,
      sort: "latest_added_at",
    }),
    getDocumentsPage({ direction: "desc", page: 1, pageSize: 5, sort: "modified_at" }),
  ]).catch(() => null);
  const dashboard = data?.[0] ?? null;
  const recentCompaniesPage = data?.[1] ?? null;
  const documentsPage = data?.[2] ?? null;

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="dashboard" />
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium text-muted-foreground">
                Local job search tracker
              </p>
              <h1 className="text-3xl font-semibold tracking-normal">Dashboard</h1>
            </div>
            <ApplicationDialog />
          </div>
        </header>

        {dashboard === null ? (
          <Card>
            <CardHeader>
              <CardTitle>Backend API unavailable</CardTitle>
              <CardDescription className="break-all">
                Could not connect to {apiBaseUrl}. Start the backend and refresh the page.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <code className="rounded-md bg-muted px-3 py-2 text-sm">
                ./scripts/start-backend.sh
              </code>
              <code className="rounded-md bg-muted px-3 py-2 text-sm">
                .\scripts\start-backend.ps1
              </code>
            </CardContent>
          </Card>
        ) : (
          <>
            <section className="grid gap-4 lg:grid-cols-2">
              <SeniorityStatsCard
                title="All time: applications / positions"
                description="Distribution of all saved applications."
                rows={dashboard.seniority_all_time}
                total={dashboard.stats.applications_total}
              />
              <SeniorityStatsCard
                title="Today: applications / positions"
                description="Applications submitted today."
                rows={dashboard.seniority_today}
                total={dashboard.stats.applications_today}
              />
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="Total applications"
                value={dashboard.stats.applications_total}
                description="All saved applications"
                icon={BriefcaseBusiness}
              />
              <MetricCard
                title="Applications today"
                value={dashboard.stats.applications_today}
                description="Activity for today"
                icon={Building2}
              />
              <MetricCard
                title="Total updates"
                value={dashboard.stats.updates_total}
                description="Statuses, emails, events"
                icon={Inbox}
              />
              <MetricCard
                title="Updates today"
                value={dashboard.stats.updates_today}
                description="Changes for today"
                icon={FileText}
              />
            </section>

            <section>
              <Card>
                <CardHeader>
                  <CardTitle>Activity over 30 days</CardTitle>
                  <CardDescription>New applications and updates by day.</CardDescription>
                </CardHeader>
                <CardContent>
                  <ApplicationsTimelineChart data={dashboard.timeline} />
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Recent positions</CardTitle>
                  <CardDescription>Last 5 added positions.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentCompaniesTable
                    companies={recentCompaniesPage?.items ?? dashboard.recent_companies}
                    total={recentCompaniesPage?.total ?? dashboard.recent_companies.length}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-col gap-1">
                      <CardTitle>Documents</CardTitle>
                      <CardDescription className="break-all">
                        Storage folder: {dashboard.storage_dir}
                      </CardDescription>
                    </div>
                    <CreateDocumentDialog
                      iconOnly
                      triggerLabel="Create document"
                      triggerSize="sm"
                      triggerVariant="outline"
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <DashboardDocumentsTable
                    documents={documentsPage?.items ?? dashboard.documents}
                    total={documentsPage?.total ?? dashboard.documents.length}
                  />
                </CardContent>
              </Card>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
