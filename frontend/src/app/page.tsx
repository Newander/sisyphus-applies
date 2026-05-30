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
            Нет откликов за этот период.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Сеньорити</TableHead>
                <TableHead className="w-24 text-right">Отклики</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.seniority ?? "empty-seniority"}>
                  <TableCell className="font-medium">
                    {row.seniority ?? "Не указано"}
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
                Локальный трекер поиска работы
              </p>
              <h1 className="text-3xl font-semibold tracking-normal">Дашборд</h1>
            </div>
            <ApplicationDialog />
          </div>
        </header>

        {dashboard === null ? (
          <Card>
            <CardHeader>
              <CardTitle>Backend API недоступен</CardTitle>
              <CardDescription className="break-all">
                Не удалось подключиться к {apiBaseUrl}. Запусти backend и обнови страницу.
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
                title="Всё время: отклики / позиции"
                description="Распределение всех сохраненных откликов."
                rows={dashboard.seniority_all_time}
                total={dashboard.stats.applications_total}
              />
              <SeniorityStatsCard
                title="Сегодня: отклики / позиции"
                description="Отклики, отправленные за текущий день."
                rows={dashboard.seniority_today}
                total={dashboard.stats.applications_today}
              />
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="Всего подач"
                value={dashboard.stats.applications_total}
                description="Все сохраненные отклики"
                icon={BriefcaseBusiness}
              />
              <MetricCard
                title="Подачи за сегодня"
                value={dashboard.stats.applications_today}
                description="Активность за текущий день"
                icon={Building2}
              />
              <MetricCard
                title="Всего апдейтов"
                value={dashboard.stats.updates_total}
                description="Статусы, письма, события"
                icon={Inbox}
              />
              <MetricCard
                title="Апдейты за сегодня"
                value={dashboard.stats.updates_today}
                description="Изменения за текущий день"
                icon={FileText}
              />
            </section>

            <section>
              <Card>
                <CardHeader>
                  <CardTitle>Активность за 30 дней</CardTitle>
                  <CardDescription>Новые отклики и апдейты по дням.</CardDescription>
                </CardHeader>
                <CardContent>
                  <ApplicationsTimelineChart data={dashboard.timeline} />
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Последние позиции</CardTitle>
                  <CardDescription>Последние 5 добавленных позиций.</CardDescription>
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
                      <CardTitle>Документы</CardTitle>
                      <CardDescription className="break-all">
                        Storage folder: {dashboard.storage_dir}
                      </CardDescription>
                    </div>
                    <CreateDocumentDialog
                      iconOnly
                      triggerLabel="Создать документ"
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
