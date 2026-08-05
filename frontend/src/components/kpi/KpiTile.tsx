export function KpiTile({ label, value, help }: { label: string; value: string; help?: string }) {
  return (
    <div className="card p-4" title={help}>
      <div className="text-muted text-xs">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}
