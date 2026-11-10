import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDate } from "./format";
import type { CurvePoint } from "./types";

const AXIS = { stroke: "var(--axis)", fontSize: 12, tick: { fill: "var(--text-muted)" } };
const TOOLTIP = {
  contentStyle: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--text-primary)",
    fontSize: 13,
  },
};

const CURVE_LINES = [
  { key: "today", name: "Today", color: "var(--series-1)", dash: undefined },
  { key: "month_ago", name: "1 month ago", color: "var(--series-2)", dash: "6 4" },
  { key: "year_ago", name: "1 year ago", color: "var(--series-3)", dash: "2 3" },
] as const;

export function YieldCurveChart({ data }: { data: CurvePoint[] }) {
  const pct = (v: number) => `${v.toFixed(2)}%`;
  return (
    <figure className="chart">
      <div className="chart-plot" role="img" aria-label="Yield curve line chart. Exact values are in the table below.">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="tenor_years" type="number" domain={[1, 11]} ticks={[2, 5, 10]}
              tickFormatter={(v) => `${v}Y`} {...AXIS} />
            <YAxis domain={[(lo: number) => Math.floor(lo * 2) / 2, (hi: number) => Math.ceil(hi * 2) / 2]}
              tickCount={5} tickFormatter={(v) => `${v.toFixed(1)}%`} width={48} {...AXIS} />
            <Tooltip {...TOOLTIP} labelFormatter={(v) => `${v}-year`} formatter={(v) => pct(Number(v))} />
            <Legend verticalAlign="top" height={28} iconType="plainline"
              itemSorter={(item) => CURVE_LINES.findIndex((l) => l.key === item.dataKey)}
              formatter={(value) => <span className="legend-text">{value}</span>} />
            {CURVE_LINES.map((l) => (
              <Line key={l.key} dataKey={l.key} name={l.name} stroke={l.color} strokeWidth={2}
                strokeDasharray={l.dash} dot={{ r: 4, fill: l.color, stroke: "var(--surface)", strokeWidth: 2, strokeDasharray: "0" }}
                activeDot={{ r: 5 }} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="curve-table">
        <caption className="sr-only">Benchmark bond yields by tenor</caption>
        <thead>
          <tr><th scope="col">Tenor</th>{CURVE_LINES.map((l) => <th scope="col" key={l.key}>{l.name}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.tenor}>
              <th scope="row">{p.tenor}</th>
              {CURVE_LINES.map((l) => {
                const v = p[l.key];
                return <td key={l.key}>{v === null ? "n/a" : pct(v)}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

export function SpreadChart({ data }: { data: { date: string; spread: number }[] }) {
  const values = data.map((d) => d.spread);
  const latest = data[data.length - 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const description =
    data.length === 0
      ? "No spread data available."
      : `10Y minus 2Y spread over the last year: latest ${latest.spread.toFixed(2)} percentage points on ` +
        `${formatDate(latest.date)}, range ${min.toFixed(2)} to ${max.toFixed(2)}.`;
  return (
    <figure className="chart">
      <div className="chart-plot" role="img" aria-label={description}>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 36, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="date" tickFormatter={(v) => formatDate(v, false)} minTickGap={40} {...AXIS} />
            <YAxis tickFormatter={(v) => v.toFixed(2)} width={48} {...AXIS}
              domain={[(lo: number) => Math.min(0, Math.floor(lo * 10) / 10), (hi: number) => Math.ceil(hi * 10) / 10]} />
            <ReferenceLine y={0} stroke="var(--axis)" />
            <Tooltip {...TOOLTIP} labelFormatter={(v) => formatDate(String(v))}
              formatter={(v) => [`${Number(v).toFixed(2)} pp`, "10Y − 2Y"]} />
            <Line dataKey="spread" stroke="var(--series-1)" strokeWidth={2} dot={false}
              activeDot={{ r: 4 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="chart-note">{description} Below zero means the curve is inverted.</figcaption>
    </figure>
  );
}
