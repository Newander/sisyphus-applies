"use client";

import { useCallback, useMemo, useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import Link from "next/link";

import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deleteDocument, getDocumentsPage, type DocumentItem } from "@/lib/api";
import { formatDate, formatDocumentType, formatFileSize } from "@/lib/format";

type DocumentsTableProps = {
  documents: DocumentItem[];
  total: number;
};

export function DocumentsTable({ documents: initialDocuments, total }: DocumentsTableProps) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [totalDocuments, setTotalDocuments] = useState(total);
  const [isLoading, setIsLoading] = useState(initialDocuments.length === 0);

  const columns = useMemo<DataTableColumn<DocumentItem>[]>(
    () => [
      {
        id: "name",
        header: "Документ",
        accessor: "name",
        cell: (document) => (
          <Link
            className="flex min-w-0 items-center gap-2 font-medium hover:underline"
            href={`/documents/${document.id}`}
            prefetch={false}
          >
            <FileText aria-hidden="true" />
            <span className="truncate">{document.name}</span>
          </Link>
        ),
      },
      {
        id: "document_type",
        header: "Тип",
        accessor: "document_type",
        cell: (document) => (
          <Badge variant="outline">{formatDocumentType(document.document_type)}</Badge>
        ),
      },
      {
        id: "company_name",
        header: "Компания",
        sortValue: (document) => document.company_name ?? "",
        className: "text-muted-foreground",
        cell: (document) => document.company_name ?? "Не привязан",
      },
      {
        id: "size_bytes",
        header: "Размер",
        accessor: "size_bytes",
        className: "text-muted-foreground",
        cell: (document) => formatFileSize(document.size_bytes),
      },
      {
        id: "modified_at",
        header: "Изменен",
        accessor: "modified_at",
        headerClassName: "text-right",
        className: "text-right text-muted-foreground",
        sortValue: (document) => new Date(document.modified_at),
        cell: (document) => formatDate(document.modified_at),
      },
    ],
    [],
  );

  const loadDocuments = useCallback(async (query: DataTableQuery) => {
    setIsLoading(true);
    try {
      const page = await getDocumentsPage({
        direction: query.sort?.direction ?? "desc",
        page: query.page,
        pageSize: query.pageSize,
        sort: query.sort?.columnId ?? "modified_at",
      });
      setDocuments(page.items);
      setTotalDocuments(page.total);
    } finally {
      setIsLoading(false);
    }
  }, []);

  async function removeDocument(document: DocumentItem) {
    if (!window.confirm(`Удалить документ ${document.name}?`)) {
      return;
    }

    try {
      await deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setTotalDocuments((current) => Math.max(0, current - 1));
    } catch {
      window.alert("Не удалось отправить файл в корзину.");
    }
  }

  return (
    <DataTable
      columns={columns}
      data={documents}
      emptyMessage="В папке документов пока нет файлов PDF, DOC, DOCX, RTF, TXT или MD."
      initialSort={{ columnId: "modified_at", direction: "desc" }}
      isLoading={isLoading}
      onQueryChange={loadDocuments}
      rowKey={(document) => document.id}
      totalItems={totalDocuments}
      renderActions={(document) => (
        <Button
          aria-label="Удалить"
          size="icon"
          title="Удалить"
          type="button"
          variant="destructive"
          onClick={() => void removeDocument(document)}
        >
          <Trash2 />
        </Button>
      )}
    />
  );
}
