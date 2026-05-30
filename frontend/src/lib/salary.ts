export type SalaryCurrency = "USD" | "PLN";

export type SalaryPresetId =
  | "none"
  | "lt_6000_usd"
  | "6000_8000_usd"
  | "8000_10000_usd"
  | "gte_10000_usd"
  | "custom";

export type SalaryRange = {
  minPln: number | null;
  maxPln: number | null;
};

export const DEFAULT_SALARY_CURRENCY: SalaryCurrency = "USD";

// Static approximate mid-market rate checked on 2026-05-25.
export const USD_TO_PLN_RATE = 3.66;

export const SALARY_PRESETS: Array<{
  id: SalaryPresetId;
  minUsd: number | null;
  maxUsd: number | null;
}> = [
  { id: "lt_6000_usd", minUsd: null, maxUsd: 6000 },
  { id: "6000_8000_usd", minUsd: 6000, maxUsd: 8000 },
  { id: "8000_10000_usd", minUsd: 8000, maxUsd: 10000 },
  { id: "gte_10000_usd", minUsd: 10000, maxUsd: null },
];

export function convertCurrencyAmount(
  amount: number,
  fromCurrency: SalaryCurrency,
  toCurrency: SalaryCurrency,
) {
  if (fromCurrency === toCurrency) {
    return amount;
  }

  return fromCurrency === "USD" ? amount * USD_TO_PLN_RATE : amount / USD_TO_PLN_RATE;
}

export function salaryAmountToPln(amount: number, currency: SalaryCurrency) {
  return Math.round(currency === "PLN" ? amount : amount * USD_TO_PLN_RATE);
}

export function salaryAmountFromPln(amountPln: number, currency: SalaryCurrency) {
  return Math.round(currency === "PLN" ? amountPln : amountPln / USD_TO_PLN_RATE);
}

export function presetToSalaryRange(presetId: SalaryPresetId): SalaryRange {
  const preset = SALARY_PRESETS.find((item) => item.id === presetId);
  if (!preset) {
    return { minPln: null, maxPln: null };
  }

  return {
    minPln: preset.minUsd === null ? null : salaryAmountToPln(preset.minUsd, "USD"),
    maxPln: preset.maxUsd === null ? null : salaryAmountToPln(preset.maxUsd, "USD"),
  };
}

export function salaryPresetLabel(presetId: SalaryPresetId, currency: SalaryCurrency) {
  if (presetId === "none") {
    return "Not selected";
  }

  if (presetId === "custom") {
    return "Custom amount";
  }

  const preset = SALARY_PRESETS.find((item) => item.id === presetId);
  if (!preset) {
    return presetId;
  }

  const formatAmount = (amountUsd: number) =>
    salaryAmountFromPln(salaryAmountToPln(amountUsd, "USD"), currency).toLocaleString("en-US");
  const suffix = currency === "USD" ? "$" : "PLN";

  if (preset.minUsd === null && preset.maxUsd !== null) {
    return `< ${formatAmount(preset.maxUsd)} ${suffix}`;
  }

  if (preset.minUsd !== null && preset.maxUsd === null) {
    return `${formatAmount(preset.minUsd)} ${suffix} +`;
  }

  if (preset.minUsd !== null && preset.maxUsd !== null) {
    return `${formatAmount(preset.minUsd)} - ${formatAmount(preset.maxUsd)} ${suffix}`;
  }

  return "Not selected";
}

export function salaryRangeToPreset(minPln: number | null, maxPln: number | null): SalaryPresetId {
  if (minPln === null && maxPln === null) {
    return "none";
  }

  const preset = SALARY_PRESETS.find((item) => {
    const range = presetToSalaryRange(item.id);
    return range.minPln === minPln && range.maxPln === maxPln;
  });

  return preset ? preset.id : "custom";
}

export function formatSalaryRange(
  minPln: number | null,
  maxPln: number | null,
  currency: SalaryCurrency = DEFAULT_SALARY_CURRENCY,
) {
  if (minPln === null && maxPln === null) {
    return "-";
  }

  const suffix = currency === "USD" ? "$" : "PLN";
  const formatAmount = (amountPln: number) =>
    salaryAmountFromPln(amountPln, currency).toLocaleString("en-US");

  if (minPln === null && maxPln !== null) {
    return `< ${formatAmount(maxPln)} ${suffix}`;
  }

  if (minPln !== null && maxPln === null) {
    return `${formatAmount(minPln)} ${suffix} +`;
  }

  return `${formatAmount(minPln ?? 0)} - ${formatAmount(maxPln ?? 0)} ${suffix}`;
}
