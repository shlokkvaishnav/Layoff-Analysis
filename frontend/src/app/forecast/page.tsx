import { api } from "@/lib/api";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { ConfidenceAuditPanel } from "@/components/ConfidenceAuditPanel";
import { ForecastControls } from "@/components/forecast/ForecastControls";

export default async function ForecastPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const get = (k: string) => {
    const v = sp[k];
    return Array.isArray(v) ? v[0] : v;
  };
  const segment = get("segment") ?? "overall";
  const rawGroupValue = get("group_value");
  const horizon = Number(get("horizon") ?? "3");

  const options = await api.forecastOptions();

  const groupCol = segment === "stage" ? "stage" : segment === "sector" ? "sector" : undefined;
  const resolvedGroupValue =
    groupCol === "stage"
      ? rawGroupValue ?? options.stage[0]
      : groupCol === "sector"
      ? rawGroupValue ?? options.sector[0]
      : undefined;

  const forecast = await api.forecast(groupCol, resolvedGroupValue, horizon);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Forecast</h1>
        <p className="text-muted text-sm mt-1">
          Defaults to the overall national trend — the least noisy, most defensible number. Switch to a
          Stage or (legacy) Sector cohort for a narrower comparison.
        </p>
      </div>

      <ForecastControls options={options} segment={segment} groupValue={resolvedGroupValue} horizon={horizon} />

      <section className="card p-4">
        <h2 className="font-medium mb-3">
          {forecast.label} — {forecast.months_of_history} months of history
        </h2>
        <ForecastChart data={forecast} />
      </section>

      <ConfidenceAuditPanel assumptions={forecast.confidence_audit.assumptions} />
    </div>
  );
}
