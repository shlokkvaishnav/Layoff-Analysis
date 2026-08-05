"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CountryBucket } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { colorForName } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

export function ByCountryChart({ data }: { data: CountryBucket[] }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#34302a" : "#e5e0d8";

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="country" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={70} interval={0} />
        <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as CountryBucket;
            return (
              <div className="card p-2 text-xs" style={{ borderColor: "var(--border)" }}>
                <div className="font-medium">{label}</div>
                <div>People laid off: {formatNumber(d.laid_off)}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="laid_off" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.country} fill={colorForName(d.country, theme)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
