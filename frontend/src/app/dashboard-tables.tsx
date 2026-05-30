"use client";

import { useCallback, useMemo, useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import Link from "next/link";

import { ApplicationDialog } from "@/components/application-dialog";
import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  apiBaseUrl,
  deleteDocument,
  getDocumentsPage,
  getRecentCompaniesPage,
  type DocumentItem,
  type RecentCompany,
} from "@/lib/api";
import { formatDate, formatDocumentType, formatFileSize, formatStatus } from "@/lib/format";

type RecentCompaniesTableProps = {
  companies: RecentCompany[];
  total: number;
};

type DashboardDocumentsTableProps = {
  documents: DocumentItem[];
  total: number;
};

export function RecentCompaniesTable({ companies: initialCompanies, total }: RecentCompaniesTableProps) {
  const [companies, setCompanies] = useState(initialCompanies);
  const [totalCompanies, setTotalCompanies] = useState(total);
  const [isLoading, setIsLoading] = useState(initialCompanies.length === 0);

  const columns = useMemo<DataTableColumn<RecentCompany>[]>(
    () => [
      {
        id: "company_name",
        header: "Компания",
        accessor: "company_name",
        cell: (company) => (
          <div className="flex flex-col gap-1">
            <span className="font-medium">{company.company_name}</span>
            <span className="text-xs text-muted-foreground">
              {company.applications_count} откликов
            </span>
          </div>
        ),
      },
      {
        id: "latest_position",
        header: "Позиция",
        accessor: "latest_position",
      },
      {
        id: "latest_status",
        header: "Статус",
        sortValue: (company) => formatStatus(company.latest_status),
        cell: (company) => <Badge variant="secondary">{formatStatus(company.latest_status)}</Badge>,
      },
      {
        id: "latest_added_at",
        header: "Добавлено",
        sortValue: (company) => new Date(company.latest_added_at),
        headerClassName: "text-right",
        className: "text-right text-muted-foreground",
        cell: (company) => formatDate(company.latest_added_at),
      },
    ],
    [],
  );

  const loadCompanies = useCallback(async (query: DataTableQuery) => {
    setIsLoading(true);
    try {
      const page = await getRecentCompaniesPage({
        direction: query.sort?.direction ?? "desc",
        page: query.page,
        pageSize: query.pageSize,
        sort: query.sort?.columnId ?? "latest_added_at",
      });
      setCompanies(page.items);
      setTotalCompanies(page.total);
    } finally {
      setIsLoading(false);
    }
  }, []);

  async function removeApplication(company: RecentCompany) {
    if (!window.confirm(`Удалить отклик ${company.latest_position}?`)) {
      return;
    }

    const response = await fetch(`${apiBaseUrl}/api/applications/${company.latest_application_id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      window.alert("Не удалось удалить отклик.");
      return;
    }

    setCompanies((current) =>
      current.filter((item) => item.latest_application_id !== company.latest_application_id),
    );
    setTotalCompanies((current) => Math.max(0, current - 1));
  }

  return (
    <DataTable
      columns={columns}
      data={companies}
      emptyMessage="Пока нет сохраненных откликов. После добавления заявок здесь появятся последние позиции."
      initialPageSize={5}
      initialSort={{ columnId: "latest_added_at", direction: "desc" }}
      isLoading={isLoading}
      onQueryChange={loadCompanies}
      pageSizeOptions={[5, 10, 20]}
      rowKey={(company) => company.latest_application_id}
      totalItems={totalCompanies}
      renderActions={(company) => (
        <>
          <ApplicationDialog
            applicationId={company.latest_application_id}
            triggerLabel={null}
            triggerSize="icon"
            triggerTitle="Редактировать"
            triggerVariant="outline"
          />
          <Button
            aria-label="Удалить"
            size="icon"
            title="Удалить"
            type="button"
            variant="destructive"
            onClick={() => void removeApplication(company)}
          >
            <Trash2 />
          </Button>
        </>
      )}
    />
  );
}

export function DashboardDocumentsTable({ documents: initialDocuments, total }: DashboardDocumentsTableProps) {
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
        id: "size_bytes",
        header: "Размер",
        accessor: "size_bytes",
        className: "text-muted-foreground",
        cell: (document) => formatFileSize(document.size_bytes),
      },
      {
        id: "modified_at",
        header: "Изменен",
        sortValue: (document) => new Date(document.modified_at),
        className: "text-muted-foreground",
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
      emptyMessage="В папке документов пока нет файлов PDF, DOCX, RTF, TXT или MD."
      initialPageSize={5}
      initialSort={{ columnId: "modified_at", direction: "desc" }}
      isLoading={isLoading}
      onQueryChange={loadDocuments}
      pageSizeOptions={[5, 10, 20]}
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
