"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReasonByQuarter } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { REASON_COLORS_DARK, REASON_COLORS_LIGHT, REASON_ORDER } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

export function ReasonsOverTimeChart({ data }: { data: ReasonByQuarter[] }) {
  const { theme } = useTheme();
  const colors = theme === "dark" ? REASON_COLORS_DARK : REASON_COLORS_LIGHT;
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  const reasonsPresent = REASON_ORDER.filter((r) => data.some((d) => d.reason === r));
  const byQuarter = new Map<string, Record<string, number>>();
  for (const row of data) {
    const entry = byQuarter.get(row.quarter) ?? {};
    entry[row.reason] = row.count;
    byQuarter.set(row.quarter, entry);
  }
  const chartData = Array.from(byQuarter.entries())
    .map(([quarter, counts]) => ({ quarter, ...counts }))
    .sort((a, b) => a.quarter.localeCompare(b.quarter));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="quarter" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={50} />
        <Tooltip formatter={(v) => formatNumber(Number(v))} />
        <Legend />
        {reasonsPresent.map((reason, i) => (
          <Bar
            key={reason}
            dataKey={reason}
            stackId="reasons"
            fill={colors[reason] ?? "#8A8A8A"}
            name={reason}
            radius={i === reasonsPresent.length - 1 ? [4, 4, 0, 0] : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
