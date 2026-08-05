"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SectorBucket } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { colorForName } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

const CATCHALL_COLOR = "#8A8A8A";

export function BySectorChart({ data }: { data: SectorBucket[] }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="sector" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={80} interval={0} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as SectorBucket;
            return (
              <div className="card p-2 text-xs" style={{ borderColor: "var(--border)" }}>
                <div className="font-medium">{label}</div>
                <div>People laid off: {formatNumber(d.total_laid_off)}</div>
                <div>Companies tracked: {d.company_count ?? "—"}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="total_laid_off" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell
              key={d.sector}
              fill={d.sector === "Other" || d.sector === "Unknown" ? CATCHALL_COLOR : colorForName(d.sector, theme)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
