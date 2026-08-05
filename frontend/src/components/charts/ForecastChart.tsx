"use client";

import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastResponse } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { formatDate, formatNumber } from "@/lib/format";

interface Row {
  date: string;
  historical?: number;
  naiveForecast?: number;
  naiveBase?: number;
  naiveRange?: number;
  arimaForecast?: number;
  arimaBase?: number;
  arimaRange?: number;
}

export function ForecastChart({ data }: { data: ForecastResponse }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";
  const historicalColor = theme === "dark" ? "#f0ece4" : "#171412";
  const naiveColor = theme === "dark" ? "#a89e91" : "#6b645c";
  const arimaColor = theme === "dark" ? "#d2b48c" : "#8b5a2b";

  const rows = new Map<string, Row>();
  for (const p of data.historical) {
    rows.set(p.date, { date: p.date, historical: p.value ?? undefined });
  }
  for (const p of data.naive.points) {
    const row = rows.get(p.date) ?? { date: p.date };
    row.naiveForecast = p.forecast ?? undefined;
    row.naiveBase = p.lower ?? undefined;
    row.naiveRange = p.lower !== null && p.upper !== null ? (p.upper as number) - (p.lower as number) : undefined;
    rows.set(p.date, row);
  }
  for (const p of data.arima.points) {
    const row = rows.get(p.date) ?? { date: p.date };
    row.arimaForecast = p.forecast ?? undefined;
    row.arimaBase = p.lower ?? undefined;
    row.arimaRange = p.lower !== null && p.upper !== null ? (p.upper as number) - (p.lower as number) : undefined;
    rows.set(p.date, row);
  }
  const chartData = Array.from(rows.values()).sort((a, b) => a.date.localeCompare(b.date));
  const hasArima = data.arima.points.length > 0;

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fontSize: 11 }} minTickGap={30} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip labelFormatter={(l) => formatDate(String(l))} formatter={(v) => formatNumber(Number(v))} />
        <Legend />

        {hasArima && (
          <>
            <Area dataKey="arimaBase" stackId="arima" stroke="none" fill="transparent" legendType="none" />
            <Area dataKey="arimaRange" stackId="arima" stroke="none" fill={arimaColor} fillOpacity={0.15} name="ARIMA 95% band" />
          </>
        )}
        <Area dataKey="naiveBase" stackId="naive" stroke="none" fill="transparent" legendType="none" />
        <Area dataKey="naiveRange" stackId="naive" stroke="none" fill={naiveColor} fillOpacity={0.15} name="Naive band" />

        <Line type="monotone" dataKey="historical" stroke={historicalColor} strokeWidth={2} dot={false} name="Historical" />
        <Line
          type="monotone" dataKey="naiveForecast" stroke={naiveColor} strokeWidth={2}
          strokeDasharray="6 4" dot={false} name={data.naive.model ?? "Naive"} connectNulls
        />
        {hasArima && (
          <Line
            type="monotone" dataKey="arimaForecast" stroke={arimaColor} strokeWidth={2}
            strokeDasharray="6 4" dot={false} name={data.arima.model ?? "ARIMA"} connectNulls
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
