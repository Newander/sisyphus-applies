import { ArrowLeft, FileText } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { AppNav } from "@/components/app-nav";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDocument, getDocumentPreview } from "@/lib/api";
import { formatDate, formatDocumentType, formatFileSize } from "@/lib/format";

import { DeleteDocumentButton } from "./delete-document-button";

type DocumentPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { id } = await params;
  const [document, preview] = await Promise.all([
    getDocument(id).catch(() => null),
    getDocumentPreview(id).catch(() => null),
  ]);

  if (document === null) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="documents" />
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Document details</p>
            <h1 className="break-all text-3xl font-semibold tracking-normal">{document.name}</h1>
          </div>
        </header>

        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <FileText aria-hidden="true" />
              <div className="min-w-0">
                <CardTitle className="break-all">{document.name}</CardTitle>
                <CardDescription className="break-all">{document.path}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 md:grid-cols-4">
              <div className="rounded-md border p-4">
                <dt className="text-sm text-muted-foreground">Type</dt>
                <dd className="mt-2">
                  <Badge variant="outline">{formatDocumentType(document.document_type)}</Badge>
                </dd>
              </div>
              <div className="rounded-md border p-4">
                <dt className="text-sm text-muted-foreground">Company</dt>
                <dd className="mt-2 font-medium">{document.company_name ?? "Not linked"}</dd>
              </div>
              <div className="rounded-md border p-4">
                <dt className="text-sm text-muted-foreground">Size</dt>
                <dd className="mt-2 font-medium">{formatFileSize(document.size_bytes)}</dd>
              </div>
              <div className="rounded-md border p-4">
                <dt className="text-sm text-muted-foreground">Modified</dt>
                <dd className="mt-2 font-medium">{formatDate(document.modified_at)}</dd>
              </div>
            </dl>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link className={buttonVariants({ variant: "outline", size: "sm" })} href="/documents">
                <ArrowLeft data-icon="inline-start" />
                Back to documents
              </Link>
              <DeleteDocumentButton documentId={document.id} documentName={document.name} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Content preview</CardTitle>
            <CardDescription>First 50 lines of the file. TXT, MD, RTF, and DOCX are supported.</CardDescription>
          </CardHeader>
          <CardContent>
            {preview?.unsupported_reason ? (
              <div className="flex min-h-32 items-center justify-center rounded-md border border-dashed p-6">
                <p className="max-w-md text-center text-sm text-muted-foreground">
                  {preview.unsupported_reason}
                </p>
              </div>
            ) : preview && preview.lines.length > 0 ? (
              <div className="max-h-[32rem] overflow-auto rounded-md border bg-muted/40">
                <pre className="min-w-full p-4 text-sm leading-6">
                  <code>
                    {preview.lines.map((line, index) => (
                      <span className="grid grid-cols-[3rem_1fr] gap-4" key={`${index}-${line}`}>
                        <span className="select-none text-right text-muted-foreground">
                          {index + 1}
                        </span>
                        <span className="break-all">{line || " "}</span>
                      </span>
                    ))}
                    {preview.truncated ? (
                      <span className="mt-2 block text-muted-foreground">
                        ... first 50 lines shown
                      </span>
                    ) : null}
                  </code>
                </pre>
              </div>
            ) : (
              <div className="flex min-h-32 items-center justify-center rounded-md border border-dashed p-6">
                <p className="max-w-md text-center text-sm text-muted-foreground">
                  Preview is empty or the file could not be read.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
