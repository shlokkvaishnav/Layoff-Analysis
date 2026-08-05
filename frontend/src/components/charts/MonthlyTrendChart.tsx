"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MonthlyPoint } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { formatMonth, formatNumber } from "@/lib/format";

export function MonthlyTrendChart({ data }: { data: MonthlyPoint[] }) {
  const { theme } = useTheme();
  const lineColor = theme === "dark" ? "#D2B48C" : "#8B5A2B";
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="month" tickFormatter={formatMonth} tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          formatter={(value) => [formatNumber(Number(value)), "People laid off"]}
          labelFormatter={(label) => formatMonth(String(label))}
        />
        <Line type="monotone" dataKey="laid_off" stroke={lineColor} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
