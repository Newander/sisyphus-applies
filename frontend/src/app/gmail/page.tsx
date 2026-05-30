import { AppNav } from "@/components/app-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getGmailMessagesPage, getGmailStatus } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { GmailMessagesTable } from "./gmail-messages-table";
import { GmailSyncButton } from "./sync-button";

export default async function GmailPage() {
  const [status, messagesPage] = await Promise.all([
    getGmailStatus(),
    getGmailMessagesPage({ direction: "desc", page: 1, pageSize: 10, sort: "internal_date" }),
  ]);

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="gmail" />
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Google Mail import</p>
            <h1 className="text-3xl font-semibold tracking-normal">Gmail</h1>
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Подключение</CardTitle>
            <CardDescription>Доступ только к одной локально подключенной почте.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="flex items-center justify-between gap-4 rounded-md border p-3">
                <span className="text-sm text-muted-foreground">Статус</span>
                <Badge variant={status.connected ? "default" : "outline"}>
                  {status.connected ? "Connected" : "Not connected"}
                </Badge>
              </div>
              <div className="flex items-center justify-between gap-4 rounded-md border p-3">
                <span className="text-sm text-muted-foreground">Аккаунт</span>
                <span className="text-right text-sm font-medium">
                  {status.email_address ?? "not connected"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-4 rounded-md border p-3">
                <span className="text-sm text-muted-foreground">Писем в БД</span>
                <span className="text-sm font-medium">{status.messages_count}</span>
              </div>
              <div className="flex items-center justify-between gap-4 rounded-md border p-3">
                <span className="text-sm text-muted-foreground">Последний sync</span>
                <span className="text-right text-sm font-medium">
                  {status.last_sync_at ? formatDate(status.last_sync_at) : "never"}
                </span>
              </div>
              <div className="rounded-md border p-3 sm:col-span-2">
                <p className="text-sm text-muted-foreground">Query</p>
                <p className="mt-1 break-all text-sm font-medium">{status.sync_query}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <GmailSyncButton />
              {!status.connected ? (
                <p className="text-sm text-muted-foreground">
                  Сначала выполни `.\scripts\connect-gmail.ps1` из корня проекта.
                </p>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Импортированные письма</CardTitle>
            <CardDescription>Последние письма, сохраненные из Gmail API.</CardDescription>
          </CardHeader>
          <CardContent>
            <GmailMessagesTable messages={messagesPage.items} total={messagesPage.total} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
