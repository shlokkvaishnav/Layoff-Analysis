"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ForecastOptions } from "@/lib/types";

export function ForecastControls({
  options,
  segment,
  groupValue,
  horizon,
}: {
  options: ForecastOptions;
  segment: string;
  groupValue?: string;
  horizon: number;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function setParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`${pathname}?${params.toString()}`);
  }

  function setSegment(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("segment", value);
    params.delete("group_value");
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="card p-3 flex flex-wrap gap-3 items-end">
      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">Segment by</span>
        <select
          className="border rounded px-2 py-1 bg-transparent text-sm"
          style={{ borderColor: "var(--border)" }}
          value={segment}
          onChange={(e) => setSegment(e.target.value)}
        >
          <option value="overall">Overall</option>
          {options.stage.length > 0 && <option value="stage">Stage</option>}
          <option value="sector">Sector (legacy)</option>
        </select>
      </label>

      {segment === "stage" && (
        <label className="flex flex-col gap-1">
          <span className="text-muted text-xs">Stage</span>
          <select
            className="border rounded px-2 py-1 bg-transparent text-sm"
            style={{ borderColor: "var(--border)" }}
            value={groupValue ?? ""}
            onChange={(e) => setParam("group_value", e.target.value)}
          >
            {options.stage.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
      )}

      {segment === "sector" && (
        <label className="flex flex-col gap-1">
          <span className="text-muted text-xs">Sector</span>
          <select
            className="border rounded px-2 py-1 bg-transparent text-sm"
            style={{ borderColor: "var(--border)" }}
            value={groupValue ?? ""}
            onChange={(e) => setParam("group_value", e.target.value)}
          >
            {options.sector.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
      )}

      <label className="flex flex-col gap-1">
        <span className="text-muted text-xs">Forecast horizon (months): {horizon}</span>
        <input
          type="range"
          min={1}
          max={6}
          value={horizon}
          onChange={(e) => setParam("horizon", e.target.value)}
        />
      </label>
    </div>
  );
}
