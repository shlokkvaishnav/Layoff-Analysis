"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { FilterOptions } from "@/lib/types";

const selectClass = "border rounded px-2 py-1 bg-transparent text-sm";

export function FilterBar({ options }: { options: FilterOptions }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`${pathname}?${params.toString()}`);
  }

  const hasFilters = ["sector", "stage", "country", "date_from", "date_to"].some((k) => searchParams.get(k));

  return (
    <div className="card p-3 mb-4 flex flex-wrap gap-3 items-end" style={{ borderColor: "var(--border)" }}>
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">Sector</span>
        <select
          className={selectClass}
          style={{ borderColor: "var(--border)" }}
          value={searchParams.get("sector") ?? ""}
          onChange={(e) => setParam("sector", e.target.value)}
        >
          <option value="">All</option>
          {options.sectors.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">Stage</span>
        <select
          className={selectClass}
          style={{ borderColor: "var(--border)" }}
          value={searchParams.get("stage") ?? ""}
          onChange={(e) => setParam("stage", e.target.value)}
        >
          <option value="">All</option>
          {options.stages.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">Country</span>
        <select
          className={selectClass}
          style={{ borderColor: "var(--border)" }}
          value={searchParams.get("country") ?? ""}
          onChange={(e) => setParam("country", e.target.value)}
        >
          <option value="">All</option>
          {options.countries.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">From</span>
        <input
          type="date"
          className={selectClass}
          style={{ borderColor: "var(--border)" }}
          min={options.date_min ?? undefined}
          max={options.date_max ?? undefined}
          value={searchParams.get("date_from") ?? ""}
          onChange={(e) => setParam("date_from", e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">To</span>
        <input
          type="date"
          className={selectClass}
          style={{ borderColor: "var(--border)" }}
          min={options.date_min ?? undefined}
          max={options.date_max ?? undefined}
          value={searchParams.get("date_to") ?? ""}
          onChange={(e) => setParam("date_to", e.target.value)}
        />
      </label>
      {hasFilters && (
        <button
          onClick={() => router.push(pathname)}
          className="text-muted underline text-sm ml-auto"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
