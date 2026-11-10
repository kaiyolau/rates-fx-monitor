import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import data from "../public/data.json";
import { Dashboard, badgeText } from "./Dashboard";
import type { DashboardData } from "./types";

describe("Dashboard", () => {
  it("renders cards, summary badge, data-quality checks and footer from data.json", () => {
    const d = data as DashboardData;
    const html = renderToStaticMarkup(<Dashboard data={d} />);

    expect(d.cards).toHaveLength(4);
    for (const card of d.cards) expect(html).toContain(card.label);
    expect(html).toContain(badgeText(d.summary));
    for (const check of d.quality_checks) expect(html).toContain(check.check_name);
    // Status is shown as text, not only color.
    expect(html).toMatch(/Pass|Warning|Fail/);
    expect(html).toContain("Not a Bank of Canada product.");
  });
});
