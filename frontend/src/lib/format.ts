import { applicationStageLabels, type ApplicationStage } from "@/lib/application-stages";

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB"];
  let size = bytes / 1024;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

export function formatStatus(status: string) {
  return applicationStageLabels[status as ApplicationStage] ?? status;
}

export function formatDocumentType(type: string) {
  const labels: Record<string, string> = {
    cover_letter: "Cover Letter",
    cv: "CV",
    other: "Other",
    portfolio: "Portfolio",
  };

  return labels[type] ?? type;
}
