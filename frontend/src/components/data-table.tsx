"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

type SortDirection = "asc" | "desc";
type SortValue = Date | number | string | null | undefined;

export type DataTableColumn<T> = {
  id: string;
  header: ReactNode;
  accessor?: keyof T;
  cell?: (row: T) => ReactNode;
  sortValue?: (row: T) => SortValue;
  sortable?: boolean;
  className?: string;
  headerClassName?: string;
};

export type DataTableSort = {
  columnId: string;
  direction: SortDirection;
};

export type DataTableQuery = {
  page: number;
  pageSize: number;
  sort: DataTableSort | null;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string | number;
  actionsHeader?: ReactNode;
  emptyMessage: string;
  initialPageSize?: number;
  initialSort?: DataTableSort;
  isLoading?: boolean;
  onQueryChange?: (query: DataTableQuery) => void;
  pageSizeOptions?: number[];
  renderActions?: (row: T) => ReactNode;
  totalItems?: number;
};

function getColumnValue<T>(row: T, column: DataTableColumn<T>): SortValue {
  if (column.sortValue) {
    return column.sortValue(row);
  }

  if (column.accessor) {
    return row[column.accessor] as SortValue;
  }

  return null;
}

function compareValues(first: SortValue, second: SortValue) {
  if (first === second) {
    return 0;
  }

  if (first === null || first === undefined) {
    return 1;
  }

  if (second === null || second === undefined) {
    return -1;
  }

  const firstValue = first instanceof Date ? first.getTime() : first;
  const secondValue = second instanceof Date ? second.getTime() : second;

  if (typeof firstValue === "number" && typeof secondValue === "number") {
    return firstValue - secondValue;
  }

  return String(firstValue).localeCompare(String(secondValue), "ru", {
    numeric: true,
    sensitivity: "base",
  });
}

function isColumnSortable<T>(column: DataTableColumn<T>) {
  return column.sortable !== false && (column.accessor !== undefined || column.sortValue);
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  actionsHeader = "Actions",
  emptyMessage,
  initialPageSize = 10,
  initialSort,
  isLoading = false,
  onQueryChange,
  pageSizeOptions = [5, 10, 20, 50],
  renderActions,
  totalItems,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<DataTableSort | null>(initialSort ?? null);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const isServerDriven = onQueryChange !== undefined;

  const sortedData = useMemo(() => {
    if (isServerDriven || !sort) {
      return data;
    }

    const sortColumn = columns.find((column) => column.id === sort.columnId);
    if (!sortColumn) {
      return data;
    }

    return [...data].sort((first, second) => {
      const comparison = compareValues(
        getColumnValue(first, sortColumn),
        getColumnValue(second, sortColumn),
      );
      return sort.direction === "asc" ? comparison : -comparison;
    });
  }, [columns, data, isServerDriven, sort]);

  const total = totalItems ?? sortedData.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPageIndex = Math.min(pageIndex, totalPages - 1);
  const pageRows = isServerDriven
    ? sortedData
    : sortedData.slice(currentPageIndex * pageSize, currentPageIndex * pageSize + pageSize);

  useEffect(() => {
    setPageIndex(0);
  }, [pageSize, sort]);

  useEffect(() => {
    if (!onQueryChange) {
      return;
    }

    onQueryChange({
      page: currentPageIndex + 1,
      pageSize,
      sort,
    });
  }, [currentPageIndex, onQueryChange, pageSize, sort]);

  function toggleSort(column: DataTableColumn<T>) {
    if (!isColumnSortable(column)) {
      return;
    }

    setSort((current) => {
      if (current?.columnId !== column.id) {
        return { columnId: column.id, direction: "asc" };
      }

      if (current.direction === "asc") {
        return { columnId: column.id, direction: "desc" };
      }

      return null;
    });
  }

  if (!isLoading && total === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center rounded-md border border-dashed">
        <p className="max-w-sm text-center text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => {
              const sortable = isColumnSortable(column);
              const activeSort = sort?.columnId === column.id ? sort.direction : null;

              return (
                <TableHead
                  key={column.id}
                  className={cn(sortable ? "select-none" : undefined, column.headerClassName)}
                >
                  {sortable ? (
                    <Button
                      className="h-auto px-0 py-0 font-medium text-muted-foreground hover:bg-transparent"
                      type="button"
                      variant="ghost"
                      onClick={() => toggleSort(column)}
                    >
                      {column.header}
                      {activeSort === "asc" ? (
                        <ArrowUp data-icon="inline-end" />
                      ) : activeSort === "desc" ? (
                        <ArrowDown data-icon="inline-end" />
                      ) : (
                        <ArrowUpDown data-icon="inline-end" />
                      )}
                    </Button>
                  ) : (
                    column.header
                  )}
                </TableHead>
              );
            })}
            {renderActions ? (
              <TableHead className="text-right">{actionsHeader}</TableHead>
            ) : null}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={columns.length + (renderActions ? 1 : 0)}>
                <p className="py-8 text-center text-sm text-muted-foreground">Loading...</p>
              </TableCell>
            </TableRow>
          ) : (
            pageRows.map((row) => (
              <TableRow key={rowKey(row)}>
                {columns.map((column) => (
                  <TableCell key={column.id} className={column.className}>
                    {column.cell ? column.cell(row) : String(row[column.accessor as keyof T] ?? "")}
                  </TableCell>
                ))}
                {renderActions ? (
                  <TableCell>
                    <div className="flex justify-end gap-2">{renderActions(row)}</div>
                  </TableCell>
                ) : null}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <div className="flex flex-col gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <div>
          Showing {total === 0 ? 0 : currentPageIndex * pageSize + 1}-
          {Math.min((currentPageIndex + 1) * pageSize, total)} of {total}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2">
            Rows
            <select
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={pageSize}
              onChange={(event) => setPageSize(Number(event.target.value))}
            >
              {pageSizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <span>
            Page {currentPageIndex + 1} of {totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              disabled={currentPageIndex === 0}
              size="sm"
              type="button"
              variant="outline"
              onClick={() => setPageIndex((current) => Math.max(0, current - 1))}
            >
              <ChevronLeft data-icon="inline-start" />
              Back
            </Button>
            <Button
              disabled={currentPageIndex >= totalPages - 1}
              size="sm"
              type="button"
              variant="outline"
              onClick={() => setPageIndex((current) => Math.min(totalPages - 1, current + 1))}
            >
              Next
              <ChevronRight data-icon="inline-end" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
