import { api, parseFilterState } from "@/lib/api";
import { FilterBar } from "@/components/filters/FilterBar";
import { BySectorChart } from "@/components/charts/BySectorChart";
import { TreemapChart } from "@/components/charts/TreemapChart";
import { ImputationChart } from "@/components/charts/ImputationChart";
import { formatPct } from "@/lib/format";

export default async function SectorPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const filters = parseFilterState(sp);

  const [options, breakdown, treemap, imputation] = await Promise.all([
    api.filterOptions(),
    api.sectorBreakdown(filters),
    api.sectorTreemap(filters),
    api.sectorImputation(filters),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Sector & Company Detail</h1>
      <FilterBar options={options} />

      <div className="card p-3 text-sm border-l-4" style={{ borderLeftColor: "#b45309" }}>
        ⚠️ {formatPct(breakdown.other_unknown_pct)} of tracked layoffs (by headcount) fall in an unclassified
        sector (Other/Unknown) — treat sector-level conclusions here with that in mind. The Trend tab&apos;s
        Stage/Country views don&apos;t have this problem.
      </div>

      <section className="card p-4">
        <h2 className="font-medium mb-3">Layoffs by Sector (vs. Companies Tracked)</h2>
        <BySectorChart data={breakdown.buckets} />
      </section>

      <section className="card p-4">
        <h2 className="font-medium mb-3">Company Hierarchy (Treemap)</h2>
        <TreemapChart data={treemap} />
      </section>

      <section className="card p-4">
        <h2 className="font-medium mb-3">Data Integrity: Reported vs Imputed</h2>
        <ImputationChart data={imputation} />
      </section>
    </div>
  );
}
