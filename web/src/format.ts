import type { Metric } from "./types";

const MINUS = "−";

function signed(text: string, value: number): string {
  if (value > 0) return `+${text}`;
  if (value < 0) return `${MINUS}${text}`;
  return text;
}

export function formatValue(m: Metric): string {
  return m.kind === "rate" ? `${m.latest_value.toFixed(2)}%` : m.latest_value.toFixed(4);
}

/** Day-over-day change: basis points for rates, CAD and percent for FX. */
export function formatChange(m: Metric): string {
  if (m.change_1d === null) return "No prior value";
  if (m.kind === "rate") {
    const bps = Math.round(m.change_1d * 100);
    if (bps === 0) return "Unchanged";
    return `${signed(String(Math.abs(bps)), bps)} ${Math.abs(bps) === 1 ? "bp" : "bps"}`;
  }
  const pct = m.pct_change_1d ?? 0;
  if (m.change_1d === 0) return "Unchanged";
  return `${signed(Math.abs(m.change_1d).toFixed(4), m.change_1d)} (${signed(Math.abs(pct).toFixed(2), pct)}%)`;
}

export function direction(m: Metric): "up" | "down" | "flat" {
  if (!m.change_1d || Math.abs(m.change_1d) < 1e-9) return "flat";
  return m.change_1d > 0 ? "up" : "down";
}

export function formatDate(iso: string, withYear = true): string {
  // Dates in data.json are calendar dates; parse at noon UTC to avoid timezone shifts.
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-CA", {
    month: "short",
    day: "numeric",
    ...(withYear ? { year: "numeric" } : {}),
    timeZone: "UTC",
  });
}

export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-CA", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/Toronto",
    timeZoneName: "short",
  });
}
