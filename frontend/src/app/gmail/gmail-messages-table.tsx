"use client";

import { useCallback, useMemo, useState } from "react";
import { Mail, Trash2 } from "lucide-react";

import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { deleteGmailMessage, getGmailMessagesPage, type GmailMessage } from "@/lib/api";
import { formatDate } from "@/lib/format";

type GmailMessagesTableProps = {
  messages: GmailMessage[];
  total: number;
};

export function GmailMessagesTable({ messages: initialMessages, total }: GmailMessagesTableProps) {
  const [messages, setMessages] = useState(initialMessages);
  const [totalMessages, setTotalMessages] = useState(total);
  const [isLoading, setIsLoading] = useState(initialMessages.length === 0);

  const columns = useMemo<DataTableColumn<GmailMessage>[]>(
    () => [
      {
        id: "subject",
        header: "Письмо",
        sortValue: (message) => message.subject ?? "",
        cell: (message) => (
          <div className="flex min-w-0 flex-col gap-1">
            <div className="flex items-center gap-2">
              <Mail aria-hidden="true" className="size-4 shrink-0 text-muted-foreground" />
              <span className="truncate font-medium">{message.subject ?? "(без темы)"}</span>
            </div>
            <p className="line-clamp-2 text-xs text-muted-foreground">{message.snippet}</p>
          </div>
        ),
      },
      {
        id: "sender",
        header: "От",
        sortValue: (message) => message.sender ?? "",
        className: "max-w-64 truncate text-muted-foreground",
        cell: (message) => message.sender,
      },
      {
        id: "internal_date",
        header: "Дата",
        sortValue: (message) => (message.internal_date ? new Date(message.internal_date) : null),
        headerClassName: "text-right",
        className: "text-right text-muted-foreground",
        cell: (message) => (message.internal_date ? formatDate(message.internal_date) : ""),
      },
    ],
    [],
  );

  const loadMessages = useCallback(async (query: DataTableQuery) => {
    setIsLoading(true);
    try {
      const page = await getGmailMessagesPage({
        direction: query.sort?.direction ?? "desc",
        page: query.page,
        pageSize: query.pageSize,
        sort: query.sort?.columnId ?? "internal_date",
      });
      setMessages(page.items);
      setTotalMessages(page.total);
    } finally {
      setIsLoading(false);
    }
  }, []);

  async function removeMessage(message: GmailMessage) {
    if (!window.confirm(`Удалить письмо ${message.subject ?? "(без темы)"}?`)) {
      return;
    }

    try {
      await deleteGmailMessage(message.id);
      setMessages((current) => current.filter((item) => item.id !== message.id));
      setTotalMessages((current) => Math.max(0, current - 1));
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Не удалось удалить письмо.");
    }
  }

  return (
    <DataTable
      columns={columns}
      data={messages}
      emptyMessage="Импортированных писем пока нет. Подключи Gmail и запусти sync."
      initialSort={{ columnId: "internal_date", direction: "desc" }}
      isLoading={isLoading}
      onQueryChange={loadMessages}
      rowKey={(message) => message.id}
      totalItems={totalMessages}
      renderActions={(message) => (
        <Button
          aria-label="Удалить"
          size="icon"
          title="Удалить"
          type="button"
          variant="destructive"
          onClick={() => void removeMessage(message)}
        >
          <Trash2 />
        </Button>
      )}
    />
  );
}
