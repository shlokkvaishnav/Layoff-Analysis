"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { StageBucket } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { STAGE_COLORS_DARK, STAGE_COLORS_LIGHT } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

export function ByStageChart({ data }: { data: StageBucket[] }) {
  const { theme } = useTheme();
  const colors = theme === "dark" ? STAGE_COLORS_DARK : STAGE_COLORS_LIGHT;
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="stage" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} interval={0} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as StageBucket;
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
            <Cell key={d.stage} fill={colors[d.stage] ?? colors.Unknown} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
