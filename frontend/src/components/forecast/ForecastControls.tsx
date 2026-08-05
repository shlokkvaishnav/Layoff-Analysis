"use client";

import { useEffect, useState } from "react";
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

  // The slider's displayed value is local state, not the `horizon` prop
  // directly -- `horizon` only updates after a full server round-trip
  // (router.push -> re-fetch), so binding the input straight to it made the
  // handle visually snap back mid-drag while that request was in flight.
  // Local state gives instant feedback; the URL (and refetch) only commits
  // once the user releases the slider.
  const [localHorizon, setLocalHorizon] = useState(horizon);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocalHorizon(horizon);
  }, [horizon]);

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
        <span className="text-muted text-xs">Forecast horizon (months): {localHorizon}</span>
        <input
          type="range"
          min={1}
          max={6}
          value={localHorizon}
          onChange={(e) => setLocalHorizon(Number(e.target.value))}
          onMouseUp={(e) => setParam("horizon", (e.target as HTMLInputElement).value)}
          onTouchEnd={(e) => setParam("horizon", (e.target as HTMLInputElement).value)}
          onKeyUp={(e) => setParam("horizon", (e.target as HTMLInputElement).value)}
        />
      </label>
    </div>
  );
}
