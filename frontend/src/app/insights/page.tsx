import { api } from "@/lib/api";
import { formatNumber, formatPct } from "@/lib/format";

// Every number on this page is computed from the same live API the rest of
// the site uses -- no hardcoded or illustrative figures.
export default async function InsightsPage() {
  const [summary, byStage, byCountry, sectorBreakdown, reasons, forecast] = await Promise.all([
    api.summary(),
    api.trendByStage(),
    api.trendByCountry({}, 5),
    api.sectorBreakdown(),
    api.reasonsFrequency(),
    api.forecast(),
  ]);

  const total = summary.people_affected_sum;

  const topStage = [...byStage]
    .filter((s) => s.stage !== "Unknown" && s.total_laid_off != null)
    .sort((a, b) => (b.total_laid_off ?? 0) - (a.total_laid_off ?? 0))[0];

  const topCountry = [...byCountry].sort((a, b) => (b.laid_off ?? 0) - (a.laid_off ?? 0))[0];

  const topReason = reasons.counts[0];

  const imputedPct = summary.total_rows ? (summary.imputed_rows / summary.total_rows) * 100 : 0;

  const lastHistorical = forecast.historical.filter((p) => p.value != null).slice(-1)[0]?.value ?? null;
  const nextForecast = forecast.naive.points[0]?.forecast ?? null;
  const direction =
    lastHistorical != null && nextForecast != null
      ? nextForecast > lastHistorical * 1.05
        ? "up"
        : nextForecast < lastHistorical * 0.95
        ? "down"
        : "flat"
      : null;

  const cards: { title: string; body: string }[] = [];

  if (topStage) {
    cards.push({
      title: "Funding stage concentration",
      body: `${topStage.stage} accounts for ${formatNumber(topStage.total_laid_off)} people laid off — the largest single funding-stage bucket, out of ${formatNumber(total)} total tracked. Sector/Industry alone would not surface this: its own largest bucket is an unclassified "Other" catch-all.`,
    });
  }

  cards.push({
    title: "Sector data has a real blind spot",
    body: `${formatPct(sectorBreakdown.other_unknown_pct)} of tracked layoffs (by headcount) fall into an unclassified sector. Any conclusion drawn from sector alone should be treated as partial — Stage and Country are more complete lenses on this same data.`,
  });

  if (topCountry) {
    const pct = total ? ((topCountry.laid_off ?? 0) / total) * 100 : 0;
    cards.push({
      title: "Geographic concentration",
      body: `${topCountry.country} alone accounts for ${formatPct(pct)} of all tracked headcount reductions — consistent with tech employment being concentrated there rather than layoffs being globally uniform.`,
    });
  }

  if (topReason && reasons.coverage_pct > 0) {
    cards.push({
      title: "Stated reasons (partial coverage)",
      body: `Among articles tagged so far (${formatPct(reasons.coverage_pct)} of rows), "${topReason.reason}" is the most commonly cited reason, mentioned ${topReason.count} times. This coverage is intentionally small and grows daily — read it as directional, not exhaustive.`,
    });
  }

  cards.push({
    title: "Data completeness",
    body: `${formatPct(imputedPct)} of rows have an imputed (not directly reported) headcount figure, filled from percentage-of-workforce or sector-median estimates rather than left blank. This is disclosed per-row, not smoothed away.`,
  });

  if (direction) {
    const label = direction === "up" ? "an increase" : direction === "down" ? "a decrease" : "roughly flat activity";
    cards.push({
      title: "Near-term outlook",
      body: `The naive baseline forecast projects ${label} over the next month relative to the most recent observed month. This model deliberately does not auto-tune — see the Forecast page's confidence audit for what would break it.`,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Insights</h1>
        <p className="text-muted text-sm mt-1">
          Data-derived observations, computed live from the same API backing every other page —
          not illustrative copy. Each one names its own limitation rather than overstating certainty.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        {cards.map((c) => (
          <div key={c.title} className="card p-5">
            <h2 className="font-medium mb-2" style={{ color: "var(--accent)" }}>
              {c.title}
            </h2>
            <p className="text-sm text-muted leading-relaxed">{c.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
