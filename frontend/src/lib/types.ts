// Mirrors backend/app/models/*.py 1:1.

export interface SummaryResponse {
  total_rows: number;
  people_affected_sum: number;
  distinct_companies: number;
  imputed_rows: number;
}

export interface FreshnessResponse {
  last_refreshed_at: string | null;
  source: string | null;
  row_count: number | null;
}

export interface FilterOptions {
  sectors: string[];
  stages: string[];
  countries: string[];
  date_min: string | null;
  date_max: string | null;
}

export interface MonthlyPoint {
  month: string;
  laid_off: number | null;
}

export interface MovingAveragePoint {
  date: string;
  laid_off: number | null;
  moving_avg: number | null;
}

export interface StageBucket {
  stage: string;
  total_laid_off: number | null;
  company_count: number | null;
}

export interface CountryBucket {
  country: string;
  laid_off: number | null;
}

export interface SectorBucket {
  sector: string;
  total_laid_off: number | null;
  company_count: number | null;
}

export interface SectorBreakdown {
  buckets: SectorBucket[];
  other_unknown_pct: number;
}

export interface TreemapCompany {
  company: string;
  laid_off: number | null;
}

export interface TreemapSector {
  sector: string;
  total: number;
  companies: TreemapCompany[];
}

export interface TreemapResponse {
  sectors: TreemapSector[];
}

export interface ImputationResponse {
  overall: { reported: number; imputed: number };
  monthly: { month: string; source_type: string; laid_off: number | null }[];
}

export interface ReasonSummary {
  coverage_pct: number;
  tagged_rows: number;
  total_rows: number;
}

export interface ReasonCount {
  reason: string;
  count: number;
}

export interface ReasonFrequencyResponse {
  coverage_pct: number;
  counts: ReasonCount[];
}

export interface ReasonByStage {
  stage: string;
  reason: string;
  count: number;
}

export interface ReasonByQuarter {
  quarter: string;
  reason: string;
  count: number;
}

export interface HistoricalPoint {
  date: string;
  value: number | null;
}

export interface ForecastPoint {
  date: string;
  forecast: number | null;
  lower: number | null;
  upper: number | null;
}

export interface ForecastSeries {
  model: string | null;
  points: ForecastPoint[];
  unavailable_reason: string | null;
}

export interface ConfidenceAssumption {
  assumption: string;
  shaky_if: string;
  risk_level: string;
}

export interface ForecastResponse {
  label: string;
  months_of_history: number;
  historical: HistoricalPoint[];
  naive: ForecastSeries;
  arima: ForecastSeries;
  confidence_audit: { assumptions: ConfidenceAssumption[] };
}

export interface ForecastOptions {
  overall: boolean;
  stage: string[];
  sector: string[];
}

export interface PaginatedRaw {
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
}

export interface FilterState {
  sector?: string;
  stage?: string;
  country?: string;
  date_from?: string;
  date_to?: string;
}
