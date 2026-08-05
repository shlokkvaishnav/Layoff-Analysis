"use client";

import { CartesianGrid, ComposedChart, Line, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis } from "recharts";
import type { MovingAveragePoint } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { formatDate, formatNumber } from "@/lib/format";

export function MovingAverageChart({ data }: { data: MovingAveragePoint[] }) {
  const { theme } = useTheme();
  const lineColor = theme === "dark" ? "#D2B48C" : "#8B5A2B";
  const dotColor = theme === "dark" ? "#6b645c" : "#a89e91";
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fontSize: 12 }} minTickGap={40} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          labelFormatter={(l) => formatDate(String(l))}
          formatter={(v, name) => [formatNumber(Number(v)), name === "laid_off" ? "Daily" : "30-day avg"]}
        />
        <Scatter dataKey="laid_off" fill={dotColor} fillOpacity={0.5} />
        <Line type="monotone" dataKey="moving_avg" stroke={lineColor} strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
