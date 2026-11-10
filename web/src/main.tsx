import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Dashboard } from "./Dashboard";
import type { DashboardData } from "./types";
import "./styles.css";

function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    // Same-origin static file written by the pipeline; no external API calls.
    fetch("/data.json", { cache: "no-cache" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setData)
      .catch(() => setError(true));
  }, []);

  if (error) return <p className="loading" role="alert">Could not load data.json.</p>;
  if (!data) return <p className="loading">Loading…</p>;
  return <Dashboard data={data} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
