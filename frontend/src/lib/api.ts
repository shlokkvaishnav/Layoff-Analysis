import type {
  CountryBucket,
  FilterOptions,
  FilterState,
  ForecastOptions,
  ForecastResponse,
  FreshnessResponse,
  ImputationResponse,
  MonthlyPoint,
  MovingAveragePoint,
  PaginatedRaw,
  ReasonByQuarter,
  ReasonByStage,
  ReasonFrequencyResponse,
  ReasonSummary,
  SectorBreakdown,
  StageBucket,
  SummaryResponse,
  TreemapResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function parseFilterState(sp: Record<string, string | string[] | undefined>): FilterState {
  const get = (k: string) => {
    const v = sp[k];
    return Array.isArray(v) ? v[0] : v;
  };
  return {
    sector: get("sector") || undefined,
    stage: get("stage") || undefined,
    country: get("country") || undefined,
    date_from: get("date_from") || undefined,
    date_to: get("date_to") || undefined,
  };
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&");
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status} for ${path}`);
  }
  return res.json() as Promise<T>;
}

function filterQs(filters: FilterState, extra: Record<string, string | number | undefined> = {}) {
  return qs({
    sector: filters.sector,
    stage: filters.stage,
    country: filters.country,
    date_from: filters.date_from,
    date_to: filters.date_to,
    ...extra,
  });
}

export const api = {
  health: () => getJson<{ status: string }>("/api/meta/health"),
  summary: (f: FilterState = {}) => getJson<SummaryResponse>(`/api/meta/summary${filterQs(f)}`),
  freshness: () => getJson<FreshnessResponse>("/api/meta/freshness"),
  filterOptions: () => getJson<FilterOptions>("/api/meta/filters"),

  trendMonthly: (f: FilterState = {}) => getJson<MonthlyPoint[]>(`/api/trend/monthly${filterQs(f)}`),
  trendMovingAverage: (f: FilterState = {}, windowDays = 30) =>
    getJson<MovingAveragePoint[]>(`/api/trend/moving-average${filterQs(f, { window_days: windowDays })}`),
  trendByStage: (f: FilterState = {}) => getJson<StageBucket[]>(`/api/trend/by-stage${filterQs(f)}`),
  trendByCountry: (f: FilterState = {}, topN = 10) =>
    getJson<CountryBucket[]>(`/api/trend/by-country${filterQs(f, { top_n: topN })}`),

  sectorBreakdown: (f: FilterState = {}) => getJson<SectorBreakdown>(`/api/sector/breakdown${filterQs(f)}`),
  sectorTreemap: (f: FilterState = {}) => getJson<TreemapResponse>(`/api/sector/treemap${filterQs(f)}`),
  sectorImputation: (f: FilterState = {}) => getJson<ImputationResponse>(`/api/sector/imputation${filterQs(f)}`),

  reasonsSummary: (f: FilterState = {}) => getJson<ReasonSummary>(`/api/reasons/summary${filterQs(f)}`),
  reasonsFrequency: (f: FilterState = {}) =>
    getJson<ReasonFrequencyResponse>(`/api/reasons/frequency${filterQs(f)}`),
  reasonsByStage: (f: FilterState = {}) => getJson<ReasonByStage[]>(`/api/reasons/by-stage${filterQs(f)}`),
  reasonsOverTime: (f: FilterState = {}) => getJson<ReasonByQuarter[]>(`/api/reasons/over-time${filterQs(f)}`),

  forecastOptions: () => getJson<ForecastOptions>("/api/forecast/options"),
  forecast: (groupCol?: string, groupValue?: string, horizon = 3) =>
    getJson<ForecastResponse>(
      `/api/forecast${qs({ group_col: groupCol, group_value: groupValue, horizon })}`,
    ),

  raw: (f: FilterState = {}, page = 1, pageSize = 50, sortBy = "date", sortDir = "desc") =>
    getJson<PaginatedRaw>(
      `/api/raw${filterQs(f, { page, page_size: pageSize, sort_by: sortBy, sort_dir: sortDir })}`,
    ),
  rawExportUrl: (f: FilterState = {}) => `${BASE_URL}/api/raw/export.csv${filterQs(f)}`,
};
