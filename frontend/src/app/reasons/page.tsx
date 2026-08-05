import { api, parseFilterState } from "@/lib/api";
import { FilterBar } from "@/components/filters/FilterBar";
import { KpiTile } from "@/components/kpi/KpiTile";
import { ReasonsFrequencyChart } from "@/components/charts/ReasonsFrequencyChart";
import { ReasonsOverTimeChart } from "@/components/charts/ReasonsOverTimeChart";
import { formatPct } from "@/lib/format";

export default async function ReasonsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const filters = parseFilterState(sp);

  const [options, summary, frequency, overTime] = await Promise.all([
    api.filterOptions(),
    api.reasonsSummary(filters),
    api.reasonsFrequency(filters),
    api.reasonsOverTime(filters),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Stated Reasons</h1>
        <p className="text-muted text-sm mt-1">
          Reasons are extracted from each layoff&apos;s own linked news source with simple keyword tagging
          (not real NLP) — deliberately naive so the limits of the method stay visible instead of trusting a
          black box.
        </p>
      </div>

      <FilterBar options={options} />

      <KpiTile
        label="Reason-Tag Coverage"
        value={formatPct(summary.coverage_pct)}
        help={`${summary.tagged_rows} of ${summary.total_rows} filtered rows have at least one tagged reason`}
      />

      {frequency.counts.length > 0 ? (
        <>
          <section className="card p-4">
            <h2 className="font-medium mb-3">Reason Frequency</h2>
            <ReasonsFrequencyChart data={frequency.counts} />
          </section>
          <section className="card p-4">
            <h2 className="font-medium mb-3">Reasons Over Time</h2>
            <ReasonsOverTimeChart data={overTime} />
          </section>
        </>
      ) : (
        <div className="card p-4 text-muted text-sm">
          No articles tagged yet for the current filter. Reason-tagging runs as part of the scheduled data
          refresh, and coverage compounds over time.
        </div>
      )}
    </div>
  );
}
