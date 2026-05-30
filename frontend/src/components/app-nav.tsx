import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Дашборд", key: "dashboard" },
  { href: "/companies", label: "Компании", key: "companies" },
  { href: "/applications", label: "Отклики", key: "applications" },
  { href: "/documents", label: "Документы", key: "documents" },
  { href: "/features", label: "Фичи", key: "features" },
  { href: "/gmail", label: "Gmail", key: "gmail" },
  { href: "/codex", label: "Codex", key: "codex" },
  { href: "/prompts", label: "Промпты", key: "prompts" },
];

type AppNavSection =
  | "dashboard"
  | "companies"
  | "applications"
  | "documents"
  | "features"
  | "gmail"
  | "codex"
  | "prompts";

export function AppNav({ active }: { active: AppNavSection }) {
  return (
    <nav
      aria-label="Основная навигация"
      className="flex w-fit flex-wrap gap-1 rounded-lg border bg-card p-1 shadow-sm"
    >
      {navItems.map((item) => {
        const isActive = active === item.key;

        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={cn(
              buttonVariants({ variant: isActive ? "default" : "ghost", size: "sm" }),
              "min-w-24",
            )}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
