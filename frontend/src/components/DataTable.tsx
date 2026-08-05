const DISPLAY_COLUMNS = ["date", "company", "sector", "stage", "country", "laid_off", "location_hq"];

export function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) {
    return <div className="text-muted text-sm p-4">No rows for the current filters.</div>;
  }
  const columns = DISPLAY_COLUMNS.filter((c) => c in rows[0]);

  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b" style={{ borderColor: "var(--border)" }}>
            {columns.map((c) => (
              <th key={c} className="text-left px-3 py-2 text-muted font-medium whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b last:border-0" style={{ borderColor: "var(--border)" }}>
              {columns.map((c) => (
                <td key={c} className="px-3 py-2 whitespace-nowrap">
                  {row[c] === null || row[c] === undefined ? "—" : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
