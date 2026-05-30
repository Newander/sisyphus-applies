import { AppNav } from "@/components/app-nav";
import { CreateDocumentDialog } from "@/components/create-document-dialog";
import { ReindexButton } from "@/components/reindex-button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboard, getDocumentsPage } from "@/lib/api";
import { DocumentsTable } from "./documents-table";

export default async function DocumentsPage() {
  const [documentsPage, dashboard] = await Promise.all([
    getDocumentsPage({ direction: "desc", page: 1, pageSize: 10, sort: "modified_at" }),
    getDashboard(),
  ]);

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="documents" />
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium text-muted-foreground">File storage</p>
              <h1 className="text-3xl font-semibold tracking-normal">Documents</h1>
            </div>
            <div className="flex gap-2">
              <ReindexButton />
              <CreateDocumentDialog triggerLabel="Create document" />
            </div>
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Files</CardTitle>
            <CardDescription className="break-all">
              Storage folder: {dashboard.storage_dir}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentsTable documents={documentsPage.items} total={documentsPage.total} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
