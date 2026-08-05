import type { ConfidenceAssumption } from "@/lib/types";

const RISK_COLOR: Record<string, string> = {
  HIGH: "#b45309",
  MEDIUM: "#a16207",
  LOW: "#4d7c0f",
};

export function ConfidenceAuditPanel({ assumptions }: { assumptions: ConfidenceAssumption[] }) {
  return (
    <div className="card p-4">
      <h3 className="font-medium mb-3">Confidence Audit</h3>
      <div className="space-y-3">
        {assumptions.map((a, i) => (
          <div key={i} className="text-sm">
            <span
              className="inline-block text-xs font-semibold px-2 py-0.5 rounded mr-2"
              style={{ backgroundColor: RISK_COLOR[a.risk_level] ?? "#8A8A8A", color: "#fff" }}
            >
              {a.risk_level}
            </span>
            <span>{a.assumption}</span>
            <div className="text-muted text-xs mt-1">Shaky if: {a.shaky_if}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
