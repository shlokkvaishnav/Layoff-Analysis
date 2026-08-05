"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ImputationResponse } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { formatMonth, formatNumber } from "@/lib/format";

export function ImputationChart({ data }: { data: ImputationResponse }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";
  const reportedColor = theme === "dark" ? "#D2B48C" : "#8B5A2B";
  const imputedColor = theme === "dark" ? "#8A7561" : "#4A3728";

  const byMonth = new Map<string, { month: string; reported: number; imputed: number }>();
  for (const row of data.monthly) {
    const entry = byMonth.get(row.month) ?? { month: row.month, reported: 0, imputed: 0 };
    if (row.source_type === "reported") entry.reported = row.laid_off ?? 0;
    if (row.source_type === "imputed") entry.imputed = row.laid_off ?? 0;
    byMonth.set(row.month, entry);
  }
  const chartData = Array.from(byMonth.values()).sort((a, b) => a.month.localeCompare(b.month));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="month" tickFormatter={formatMonth} tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip labelFormatter={(l) => formatMonth(String(l))} formatter={(v) => formatNumber(Number(v))} />
        <Legend />
        <Bar dataKey="reported" stackId="a" fill={reportedColor} name="Reported" />
        <Bar dataKey="imputed" stackId="a" fill={imputedColor} name="Imputed" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
