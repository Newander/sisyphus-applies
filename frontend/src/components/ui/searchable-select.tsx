"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type Option = {
  value: string | number;
  label: string;
};

type SearchableSelectProps = {
  options: Option[];
  value: string | number | null;
  onChange: (value: string | number | null) => void;
  onSearchChange?: (search: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

export function SearchableSelect({
  options,
  value,
  onChange,
  onSearchChange,
  placeholder = "Select...",
  disabled = false,
  className,
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find((opt) => opt.value === value) ?? null;

  const filteredOptions = options.filter((opt) =>
    opt.label.toLowerCase().includes(search.toLowerCase()),
  );

  function openDropdown() {
    if (disabled) return;
    setIsOpen(true);
    setSearch("");
    if (onSearchChange) onSearchChange("");
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function closeDropdown() {
    setIsOpen(false);
    setSearch("");
    if (onSearchChange) onSearchChange("");
  }

  function selectOption(opt: Option) {
    onChange(opt.value);
    closeDropdown();
  }

  function handleSearchChange(nextSearch: string) {
    setSearch(nextSearch);
    if (onSearchChange) onSearchChange(nextSearch);
  }

  useEffect(() => {
    if (!isOpen) return;

    function handleOutsideClick(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearch("");
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [isOpen]);

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      closeDropdown();
    } else if (event.key === "Enter" && filteredOptions.length === 1) {
      selectOption(filteredOptions[0]);
    }
  }

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border bg-background px-3 text-sm transition-colors",
          isOpen && "ring-2 ring-ring ring-offset-1",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        {isOpen ? (
          <input
            ref={inputRef}
            className="h-full w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            placeholder="Search..."
            value={search}
            disabled={disabled}
            onChange={(e) => handleSearchChange(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        ) : (
          <button
            type="button"
            disabled={disabled}
            className="flex h-full w-full items-center text-left"
            onClick={openDropdown}
          >
            <span className={cn("truncate", !selectedOption && "text-muted-foreground")}>
              {selectedOption ? selectedOption.label : placeholder}
            </span>
          </button>
        )}
        <button
          type="button"
          disabled={disabled}
          tabIndex={-1}
          className="ml-2 shrink-0"
          onClick={isOpen ? closeDropdown : openDropdown}
        >
          <svg
            className={cn("h-4 w-4 text-muted-foreground transition-transform", isOpen && "rotate-180")}
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {isOpen ? (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover text-popover-foreground shadow-md">
          <ul className="max-h-52 overflow-y-auto py-1">
            {filteredOptions.length === 0 ? (
              <li className="px-3 py-2 text-sm text-muted-foreground">Nothing found</li>
            ) : (
              filteredOptions.map((opt) => (
                <li
                  key={opt.value}
                  className={cn(
                    "cursor-pointer px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                    opt.value === value && "bg-accent/50 font-medium",
                  )}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => selectOption(opt)}
                >
                  {opt.label}
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
