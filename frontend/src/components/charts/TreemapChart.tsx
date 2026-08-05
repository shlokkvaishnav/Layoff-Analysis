"use client";

import { ResponsiveContainer, Tooltip, Treemap } from "recharts";
import type { TreemapResponse } from "@/lib/types";
import { useTheme } from "@/lib/theme";
import { colorForName } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

interface TreemapCellProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  depth?: number;
  theme: "light" | "dark";
}

function TreemapCell({ x = 0, y = 0, width = 0, height = 0, name = "", depth, theme }: TreemapCellProps) {
  const fill = depth === 1 ? colorForName(name, theme) : "transparent";
  // Only label the sector (depth 1) cells -- Recharts' Treemap layout starts
  // the first child at the same corner as its parent, so labeling both
  // depths renders two strings on top of each other (e.g. "Microsoft" +
  // "Other" -> "Mibersoft"). Company names are still available via the
  // tooltip on hover.
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} style={{ fill, stroke: "var(--background)", strokeWidth: 2 }} />
      {depth === 1 && width > 60 && height > 20 && (
        <text x={x + 6} y={y + 16} fontSize={11} fill="#fff">
          {name}
        </text>
      )}
    </g>
  );
}

export function TreemapChart({ data }: { data: TreemapResponse }) {
  const { theme } = useTheme();
  const treeData = data.sectors.map((s) => ({
    name: s.sector,
    children: s.companies.map((c) => ({ name: c.company, size: c.laid_off ?? 0 })),
  }));

  return (
    <ResponsiveContainer width="100%" height={420}>
      <Treemap
        data={treeData}
        dataKey="size"
        stroke="var(--background)"
        content={<TreemapCell theme={theme} />}
      >
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as { name: string; size?: number };
            return (
              <div className="card p-2 text-xs" style={{ borderColor: "var(--border)" }}>
                <div className="font-medium">{d.name}</div>
                {d.size !== undefined && <div>{formatNumber(d.size)} laid off</div>}
              </div>
            );
          }}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
