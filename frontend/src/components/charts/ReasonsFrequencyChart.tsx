"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReasonCount } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { REASON_COLORS_DARK, REASON_COLORS_LIGHT } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

export function ReasonsFrequencyChart({ data }: { data: ReasonCount[] }) {
  const { theme } = useTheme();
  const colors = theme === "dark" ? REASON_COLORS_DARK : REASON_COLORS_LIGHT;
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="reason" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} interval={0} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={50} />
        <Tooltip formatter={(v) => [formatNumber(Number(v)), "Mentions"]} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.reason} fill={colors[d.reason] ?? "#8A8A8A"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
