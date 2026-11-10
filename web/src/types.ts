// Shape of public/data.json, written by pipeline/run.py.

export type Status = "pass" | "warn" | "fail";

export interface Metric {
  series: string;
  label: string;
  kind: "rate" | "fx";
  latest_date: string;
  latest_value: number;
  prev_date: string | null;
  change_1d: number | null;
  change_1m: number | null;
  change_1y: number | null;
  pct_change_1d: number | null;
  pct_change_1m: number | null;
  pct_change_1y: number | null;
}

export interface CurvePoint {
  tenor: string;
  tenor_years: number;
  today: number | null;
  today_date: string | null;
  month_ago: number | null;
  month_ago_date: string | null;
  year_ago: number | null;
  year_ago_date: string | null;
}

export interface QualityCheck {
  check_name: string;
  status: Status;
  message: string;
}

export interface Summary {
  text: string;
  source: "ai" | "rule_based";
  model: string | null;
  ai_status: "verified" | "rejected" | "error" | "not_configured";
  numbers_checked: number;
  numbers_verified: number;
}

export interface DashboardData {
  generated_at: string;
  as_of: string;
  source: { name: string; url: string; terms_url: string };
  cards: Metric[];
  metrics: Metric[];
  yield_curve: CurvePoint[];
  spread_history: { date: string; spread: number }[];
  quality_checks: QualityCheck[];
  summary: Summary;
}
