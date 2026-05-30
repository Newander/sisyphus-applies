"use client";

import { FormEvent, useCallback, useMemo, useState } from "react";
import { Edit2, Plus, Trash2, X } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { DataTable, type DataTableColumn, type DataTableQuery } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiBaseUrl, getCompaniesPage, type Company } from "@/lib/api";
import { formatDate } from "@/lib/format";

type CompanyForm = {
  name: string;
  website: string;
  notes: string;
};

const emptyForm: CompanyForm = {
  name: "",
  website: "",
  notes: "",
};

function toForm(company: Company): CompanyForm {
  return {
    name: company.name,
    website: company.website ?? "",
    notes: company.notes ?? "",
  };
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [form, setForm] = useState<CompanyForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const editingCompany = useMemo(
    () => companies.find((company) => company.id === editingId) ?? null,
    [companies, editingId],
  );

  const columns = useMemo<DataTableColumn<Company>[]>(
    () => [
      {
        id: "name",
        header: "Компания",
        accessor: "name",
        cell: (company) => (
          <div className="flex flex-col gap-1">
            <span className="font-medium">{company.name}</span>
            {company.website ? (
              <span className="truncate text-xs text-muted-foreground">{company.website}</span>
            ) : null}
          </div>
        ),
      },
      {
        id: "applications_count",
        header: "Отклики",
        accessor: "applications_count",
      },
      {
        id: "updated_at",
        header: "Обновлена",
        accessor: "updated_at",
        className: "text-muted-foreground",
        sortValue: (company) => new Date(company.updated_at),
        cell: (company) => formatDate(company.updated_at),
      },
    ],
    [],
  );

  const loadCompanies = useCallback(async (query: DataTableQuery) => {
    setIsLoading(true);
    setError(null);
    try {
      const page = await getCompaniesPage({
        direction: query.sort?.direction ?? "asc",
        page: query.page,
        pageSize: query.pageSize,
        sort: query.sort?.columnId ?? "name",
      });
      setCompanies(page.items);
      setTotalCompanies(page.total);
    } catch {
      setError("Не удалось загрузить компании");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reloadFirstPage = useCallback(
    () =>
      loadCompanies({
        page: 1,
        pageSize: 10,
        sort: { columnId: "name", direction: "asc" },
      }),
    [loadCompanies],
  );

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const payload = {
      name: form.name.trim(),
      website: form.website.trim() || null,
      notes: form.notes.trim() || null,
    };

    const url =
      editingId === null
        ? `${apiBaseUrl}/api/companies`
        : `${apiBaseUrl}/api/companies/${editingId}`;
    const response = await fetch(url, {
      method: editingId === null ? "POST" : "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Не удалось сохранить компанию");
      return;
    }

    resetForm();
    await reloadFirstPage();
  }

  async function deleteCompany(company: Company) {
    if (!window.confirm(`Удалить компанию ${company.name}?`)) {
      return;
    }

    const response = await fetch(`${apiBaseUrl}/api/companies/${company.id}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.detail ?? "Не удалось удалить компанию");
      return;
    }
    setCompanies((current) => current.filter((item) => item.id !== company.id));
    setTotalCompanies((current) => Math.max(0, current - 1));
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="companies" />
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Справочник</p>
            <h1 className="text-3xl font-semibold tracking-normal">Компании</h1>
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
          <Card>
            <CardHeader>
              <CardTitle>{editingCompany ? "Редактировать компанию" : "Новая компания"}</CardTitle>
              <CardDescription>Компании используются при создании откликов.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="flex flex-col gap-4" onSubmit={submitForm}>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Название
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    required
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                  />
                </label>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Сайт
                  <input
                    className="h-10 rounded-md border bg-background px-3 text-sm"
                    type="url"
                    value={form.website}
                    onChange={(event) => setForm({ ...form, website: event.target.value })}
                  />
                </label>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Заметки
                  <textarea
                    className="min-h-28 rounded-md border bg-background px-3 py-2 text-sm"
                    value={form.notes}
                    onChange={(event) => setForm({ ...form, notes: event.target.value })}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit">
                    <Plus data-icon="inline-start" />
                    {editingCompany ? "Сохранить" : "Создать"}
                  </Button>
                  {editingCompany ? (
                    <Button type="button" variant="outline" onClick={resetForm}>
                      <X data-icon="inline-start" />
                      Отменить
                    </Button>
                  ) : null}
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Список компаний</CardTitle>
              <CardDescription>{companies.length} компаний в локальной базе.</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={companies}
                emptyMessage="Компаний пока нет."
                initialSort={{ columnId: "name", direction: "asc" }}
                isLoading={isLoading}
                onQueryChange={loadCompanies}
                rowKey={(company) => company.id}
                totalItems={totalCompanies}
                renderActions={(company) => (
                  <>
                    <Button
                      aria-label="Редактировать"
                      title="Редактировать"
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => {
                        setEditingId(company.id);
                        setForm(toForm(company));
                      }}
                    >
                      <Edit2 />
                    </Button>
                    <Button
                      aria-label="Удалить"
                      title="Удалить"
                      type="button"
                      variant="destructive"
                      size="icon"
                      onClick={() => void deleteCompany(company)}
                    >
                      <Trash2 />
                    </Button>
                  </>
                )}
              />
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
