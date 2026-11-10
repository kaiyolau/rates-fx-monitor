import { SpreadChart, YieldCurveChart } from "./Charts";
import { direction, formatChange, formatDate, formatTimestamp, formatValue } from "./format";
import type { DashboardData, Status, Summary } from "./types";

export const REPO_URL = "https://github.com/kaiyolau/rates-fx-monitor";

const STATUS_TEXT: Record<Status, { icon: string; label: string }> = {
  pass: { icon: "✓", label: "Pass" },
  warn: { icon: "!", label: "Warning" },
  fail: { icon: "✕", label: "Fail" },
};

const ARROW = { up: "▲", down: "▼", flat: "■" };

export function badgeText(s: Summary): string {
  return s.source === "ai"
    ? `AI-written, ${s.numbers_verified} of ${s.numbers_checked} numbers verified against source data`
    : "Rule-based summary (AI unavailable or rejected)";
}

export function Dashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <header className="page-header">
        <h1>Rates &amp; FX Monitor</h1>
        <p className="updated">
          Last updated <time dateTime={data.generated_at}>{formatTimestamp(data.generated_at)}</time>
        </p>
        <p className="subtitle">
          Canadian policy rate, bond yields and exchange rates from Bank of Canada public data (Valet API).
        </p>
      </header>

      <main>
        <section aria-labelledby="cards-heading">
          <h2 id="cards-heading" className="sr-only">Latest values</h2>
          <ul className="cards">
            {data.cards.map((m) => {
              const dir = direction(m);
              return (
                <li className="card" key={m.series}>
                  <h3 className="card-label">{m.label}</h3>
                  <p className="card-value">{formatValue(m)}</p>
                  <p className="card-change">
                    <span aria-hidden="true" className={`arrow ${dir}`}>{ARROW[dir]}</span>{" "}
                    {formatChange(m)}
                    <span className="card-sub">
                      {" "}vs. {m.prev_date ? formatDate(m.prev_date, false) : "previous day"}
                    </span>
                  </p>
                  <p className="card-date">As of {formatDate(m.latest_date)}</p>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="panel summary" aria-labelledby="summary-heading">
          <div className="summary-head">
            <h2 id="summary-heading">What moved</h2>
            <span className={`badge ${data.summary.source}`}>{badgeText(data.summary)}</span>
          </div>
          <p className="summary-text">{data.summary.text}</p>
        </section>

        <div className="charts">
          <section className="panel" aria-labelledby="curve-heading">
            <h2 id="curve-heading">Yield curve</h2>
            <p className="panel-note">Government of Canada benchmark yields, %</p>
            <YieldCurveChart data={data.yield_curve} />
          </section>
          <section className="panel" aria-labelledby="spread-heading">
            <h2 id="spread-heading">10Y minus 2Y spread, last year</h2>
            <p className="panel-note">Percentage points</p>
            <SpreadChart data={data.spread_history} />
          </section>
        </div>

        <section className="panel" aria-labelledby="dq-heading">
          <h2 id="dq-heading">Data quality</h2>
          <p className="panel-note">SQL checks run on every pipeline run, against data as of {formatDate(data.as_of)}.</p>
          <ul className="checks">
            {data.quality_checks.map((c) => (
              <li className="check" key={c.check_name}>
                <span className={`status ${c.status}`}>
                  <span className="status-icon" aria-hidden="true">{STATUS_TEXT[c.status].icon}</span>
                  {STATUS_TEXT[c.status].label}
                </span>
                <span className="check-name">{c.check_name}</span>
                <span className="check-message">{c.message}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel" aria-labelledby="ai-heading">
          <h2 id="ai-heading">How this was built with AI</h2>
          <div className="ai-columns">
            <div>
              <h3>What I delegated to AI</h3>
              <p>Claude Code drafted the Python pipeline, SQL, React page, tests and CI workflows, following the
                rules in CLAUDE.md.</p>
            </div>
            <div>
              <h3>How I verified it</h3>
              <p>Pytest and Vitest run in CI on every push. Pipeline output was checked against raw Valet data,
                and AI mistakes are logged with how they were caught.</p>
            </div>
            <div>
              <h3>Where I chose not to rely on AI</h3>
              <p>Metrics and data-quality rules are plain SQL with stated thresholds. AI text is shown only if every
                number matches the source data; otherwise a rule-based template is used.</p>
            </div>
          </div>
          <p className="panel-note"><a href={`${REPO_URL}/blob/main/AI_WORKFLOW.md`}>Read the full AI workflow log</a></p>
        </section>
      </main>

      <footer className="page-footer">
        <p><a href={REPO_URL}>Source code on GitHub</a></p>
        <p>Unofficial demo using Bank of Canada public data. Not a Bank of Canada product.</p>
        <p><a href={data.source.terms_url}>Valet API terms of use</a></p>
      </footer>
    </>
  );
}
