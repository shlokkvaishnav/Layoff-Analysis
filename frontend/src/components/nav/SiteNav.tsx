"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/theme";

const LINKS = [
  { href: "/trend", label: "Trend" },
  { href: "/sector", label: "Sector & Company Detail" },
  { href: "/reasons", label: "Stated Reasons" },
  { href: "/forecast", label: "Forecast" },
  { href: "/insights", label: "Insights" },
  { href: "/raw", label: "Raw Data Explorer" },
];

export function SiteNav() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <header className="border-b" style={{ borderColor: "var(--border)" }}>
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-semibold whitespace-nowrap">
          Layoff Pulse
        </Link>
        <nav className="flex gap-4 text-sm overflow-x-auto">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`whitespace-nowrap pb-1 border-b-2 ${
                pathname?.startsWith(link.href) ? "border-current" : "border-transparent text-muted"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={toggle}
          className="ml-auto text-sm text-muted border rounded px-2 py-1"
          style={{ borderColor: "var(--border)" }}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </header>
  );
}
