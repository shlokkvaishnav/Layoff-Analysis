import Link from "next/link";
import { Hero3D } from "@/components/landing/Hero3D";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/format";

export default async function LandingPage() {
  const [summary, freshness] = await Promise.all([api.summary(), api.freshness()]);

  return (
    <div className="flex flex-col">
      <section className="relative left-1/2 right-1/2 -mx-[50vw] w-screen min-h-[92vh] overflow-hidden flex items-center justify-center">
        <div className="absolute inset-0">
          <Hero3D />
        </div>
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, transparent 0%, var(--background) 78%)",
          }}
        />

        <div className="glass relative z-10 max-w-3xl mx-auto text-center px-8 py-12 sm:px-14 sm:py-16 rounded-[2.5rem]">
          <p className="text-xs tracking-[0.3em] uppercase text-muted mb-5">Layoff Pulse 2026</p>
          <h1 className="text-5xl sm:text-6xl font-semibold tracking-tight leading-[1.05]">
            The tech layoff signal,{" "}
            <span style={{ color: "var(--accent)" }}>read straight</span>.
          </h1>
          <p className="mt-6 text-lg text-muted max-w-xl mx-auto">
            Trend, stated reason, and forecast for tech-sector layoffs — built on live,
            continuously refreshed data. No static spreadsheet, no smoothed-over numbers.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/trend"
              className="px-6 py-3 rounded-full font-medium transition-opacity hover:opacity-90"
              style={{ background: "var(--accent)", color: "var(--background)" }}
            >
              View the Dashboard
            </Link>
            <Link
              href="/forecast"
              className="px-6 py-3 rounded-full font-medium border"
              style={{ borderColor: "var(--border)" }}
            >
              See the Forecast
            </Link>
          </div>
        </div>
      </section>

      <section className="relative z-10 -mt-28 px-2">
        <div className="max-w-5xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Layoff events tracked" value={formatNumber(summary.total_rows)} />
          <StatCard label="People affected (sum)" value={formatNumber(summary.people_affected_sum)} />
          <StatCard label="Distinct companies" value={formatNumber(summary.distinct_companies)} />
          <StatCard label="Primary source" value={freshness.source ?? "layoffs.fyi"} small />
        </div>
        <p className="text-center text-muted text-xs mt-4">
          {freshness.last_refreshed_at
            ? `Refreshed ${new Date(freshness.last_refreshed_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} — updated daily via a scheduled live scrape, not on request.`
            : "Updated daily via a scheduled live scrape, not on request."}
        </p>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-24 grid sm:grid-cols-3 gap-8">
        <Pillar
          title="Trend"
          body="Monthly trend, 30-day moving average, and breakdowns by funding stage and country — reliable dimensions instead of a noisy sector field."
          href="/trend"
        />
        <Pillar
          title="Reason"
          body="Stated reasons extracted from each layoff's own linked news source, with a visible coverage percentage — not a black box."
          href="/reasons"
        />
        <Pillar
          title="Forecast"
          body="Naive baseline vs. ARIMA, with a confidence audit that flags exactly which assumptions are shaky."
          href="/forecast"
        />
      </section>
    </div>
  );
}

function StatCard({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className="glass rounded-2xl p-5 text-center">
      <div className={small ? "text-base font-medium" : "text-2xl font-semibold"}>{value}</div>
      <div className="text-muted text-xs mt-1">{label}</div>
    </div>
  );
}

function Pillar({ title, body, href }: { title: string; body: string; href: string }) {
  return (
    <Link href={href} className="card p-6 block hover:opacity-90 transition-opacity">
      <h3 className="font-semibold text-lg mb-2" style={{ color: "var(--accent)" }}>
        {title}
      </h3>
      <p className="text-muted text-sm leading-relaxed">{body}</p>
    </Link>
  );
}
