// Fixed categorical color assignment -- kept in lockstep with pipeline/eda.py's
// STAGE_ORDER / REASON_COLOR_MAP. A given category keeps the same color across
// any filtered view rather than being repainted by whichever order it happens
// to appear in a given slice (dataviz-skill requirement).
//
// NOTE: these hex values are a reasonable-effort categorical set (varied hue,
// consistent lightness/saturation band per theme) but have not been run
// through the dataviz skill's CVD-safety validator script -- flagged as a
// follow-up if that level of rigor is needed later.

export const STAGE_ORDER = [
  "Seed",
  "Series A",
  "Series B",
  "Series C",
  "Series D",
  "Series E+",
  "Private Equity",
  "Acquired",
  "Subsidiary",
  "Public",
  "Unknown",
] as const;

export const STAGE_COLORS_LIGHT: Record<string, string> = {
  Seed: "#8B5A2B",
  "Series A": "#B8722E",
  "Series B": "#C9962B",
  "Series C": "#5B7F4F",
  "Series D": "#2E7D6B",
  "Series E+": "#2E6B8B",
  "Private Equity": "#5B4F8B",
  Acquired: "#8B4F7A",
  Subsidiary: "#8B4F4F",
  Public: "#4F5D8B",
  Unknown: "#8A8A8A",
};

export const STAGE_COLORS_DARK: Record<string, string> = {
  Seed: "#D2B48C",
  "Series A": "#E0A868",
  "Series B": "#F0C868",
  "Series C": "#9BC98A",
  "Series D": "#6FC2AE",
  "Series E+": "#6FAFD2",
  "Private Equity": "#A79BD2",
  Acquired: "#D29BC2",
  Subsidiary: "#D29B9B",
  Public: "#9BA8D2",
  Unknown: "#B0B0B0",
};

export const REASON_ORDER = [
  "restructuring",
  "efficiency",
  "streamlin",
  "realign",
  "cost discipline",
  "AI",
  "automation",
  "macroeconomic",
  "market conditions",
  "right-sizing",
] as const;

export const REASON_COLORS_LIGHT: Record<string, string> = {
  restructuring: "#B8722E",
  efficiency: "#8B5A2B",
  streamlin: "#A67B5B",
  realign: "#C9A66B",
  "cost discipline": "#8B6F47",
  AI: "#2E6B8B",
  automation: "#5B7F4F",
  macroeconomic: "#6F4E37",
  "market conditions": "#5B4F8B",
  "right-sizing": "#4A3728",
};

export const REASON_COLORS_DARK: Record<string, string> = {
  restructuring: "#E0A868",
  efficiency: "#D2B48C",
  streamlin: "#C9A98A",
  realign: "#E0CB9E",
  "cost discipline": "#BFA678",
  AI: "#6FAFD2",
  automation: "#9BC98A",
  macroeconomic: "#A98F73",
  "market conditions": "#A79BD2",
  "right-sizing": "#8A7561",
};

// Stable hash-of-name -> palette slot for open-ended categories (countries,
// sectors) where the member set changes across filters -- so a given name's
// color doesn't repaint when the top-N set changes.
const FALLBACK_PALETTE_LIGHT = [
  "#8B5A2B", "#2E6B8B", "#5B7F4F", "#8B4F7A", "#C9962B",
  "#2E7D6B", "#5B4F8B", "#8B4F4F", "#4F5D8B", "#6F4E37",
];
const FALLBACK_PALETTE_DARK = [
  "#D2B48C", "#6FAFD2", "#9BC98A", "#D29BC2", "#F0C868",
  "#6FC2AE", "#A79BD2", "#D29B9B", "#9BA8D2", "#A98F73",
];

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function colorForName(name: string, theme: "light" | "dark"): string {
  const palette = theme === "dark" ? FALLBACK_PALETTE_DARK : FALLBACK_PALETTE_LIGHT;
  return palette[hashString(name) % palette.length];
}
