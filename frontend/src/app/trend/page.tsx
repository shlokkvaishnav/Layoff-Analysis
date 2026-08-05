import { api, parseFilterState } from "@/lib/api";
import { FilterBar } from "@/components/filters/FilterBar";
import { KpiTile } from "@/components/kpi/KpiTile";
import { MonthlyTrendChart } from "@/components/charts/MonthlyTrendChart";
import { MovingAverageChart } from "@/components/charts/MovingAverageChart";
import { ByStageChart } from "@/components/charts/ByStageChart";
import { ByCountryChart } from "@/components/charts/ByCountryChart";
import { formatNumber } from "@/lib/format";

export default async function TrendPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const filters = parseFilterState(sp);

  const [options, summary, freshness, monthly, movingAvg, byStage, byCountry] = await Promise.all([
    api.filterOptions(),
    api.summary(filters),
    api.freshness(),
    api.trendMonthly(filters),
    api.trendMovingAverage(filters),
    api.trendByStage(filters),
    api.trendByCountry(filters),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Trend</h1>
        {freshness.last_refreshed_at && (
          <p className="text-muted text-xs mt-1">
            Data as of {new Date(freshness.last_refreshed_at).toLocaleString()} — source: {freshness.source}
          </p>
        )}
      </div>

      <FilterBar options={options} />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiTile label="Total Reported Layoffs (rows)" value={formatNumber(summary.total_rows)} />
        <KpiTile label="People Affected (sum)" value={formatNumber(summary.people_affected_sum)} />
        <KpiTile label="Distinct Companies" value={formatNumber(summary.distinct_companies)} />
        <KpiTile label="Imputed Rows" value={formatNumber(summary.imputed_rows)} />
      </div>

      <section className="card p-4">
        <h2 className="font-medium mb-3">Rolling Moving Average (30-day)</h2>
        <MovingAverageChart data={movingAvg} />
      </section>

      <section className="card p-4">
        <h2 className="font-medium mb-3">Monthly Layoffs Trend</h2>
        <MonthlyTrendChart data={monthly} />
      </section>

      {byStage.length > 0 && (
        <section className="card p-4">
          <h2 className="font-medium mb-1">By Funding Stage</h2>
          <p className="text-muted text-xs mb-3">
            Funding stage is well-populated and not dominated by a catch-all bucket the way sector is — see
            the caveat on the Sector tab.
          </p>
          <ByStageChart data={byStage} />
        </section>
      )}

      {byCountry.length > 0 && (
        <section className="card p-4">
          <h2 className="font-medium mb-3">By Country</h2>
          <ByCountryChart data={byCountry} />
        </section>
      )}

      {byStage.length === 0 && byCountry.length === 0 && (
        <div className="card p-4 text-muted text-sm">
          Stage/Country breakdowns need the layoffs.fyi-shaped source (unavailable for this data source,
          e.g. WARN Act fallback).
        </div>
      )}
    </div>
  );
}
