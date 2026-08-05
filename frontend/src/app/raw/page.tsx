import { api, parseFilterState } from "@/lib/api";
import { FilterBar } from "@/components/filters/FilterBar";
import { DataTable } from "@/components/DataTable";

export default async function RawPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const filters = parseFilterState(sp);
  const page = Number(Array.isArray(sp.page) ? sp.page[0] : sp.page ?? "1");
  const pageSize = 50;

  const [options, raw] = await Promise.all([
    api.filterOptions(),
    api.raw(filters, page, pageSize),
  ]);

  const totalPages = Math.max(1, Math.ceil(raw.total / pageSize));

  const baseParams = new URLSearchParams();
  for (const [k, v] of Object.entries(sp)) {
    if (k === "page" || typeof v !== "string") continue;
    baseParams.set(k, v);
  }
  const baseQuery = baseParams.toString();
  const hrefFor = (p: number) => `?${baseQuery ? baseQuery + "&" : ""}page=${p}`;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Explore the Cleaned Dataset</h1>
        <a href={api.rawExportUrl(filters)} className="text-sm underline text-muted">
          Export filtered CSV
        </a>
      </div>

      <FilterBar options={options} />

      <DataTable rows={raw.rows} />

      <div className="flex items-center gap-3 text-sm">
        {page > 1 ? (
          <a href={hrefFor(page - 1)} className="underline">Previous</a>
        ) : (
          <span className="text-muted opacity-50">Previous</span>
        )}
        <span className="text-muted">
          Page {page} of {totalPages} ({raw.total} rows)
        </span>
        {page < totalPages ? (
          <a href={hrefFor(page + 1)} className="underline">Next</a>
        ) : (
          <span className="text-muted opacity-50">Next</span>
        )}
      </div>
    </div>
  );
}
