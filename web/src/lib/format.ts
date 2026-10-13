const int = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const acres = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const fmtInt = (n: number) => int.format(n);
export const fmtAcres = (n: number) => `${acres.format(n)} ac`;
export const fmtSqft = (n: number) => `${int.format(n)} sq ft`;

/** "2026-10-13T17:50:20+00:00" -> "Oct 13, 2026" (Pacific time, where the data lives). */
export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "unknown date";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "America/Los_Angeles",
  });
}

/** Digits-only APN -> "097-08-058". */
export function formatApn(digits: string): string {
  return digits.length === 8 ? `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}` : digits;
}
