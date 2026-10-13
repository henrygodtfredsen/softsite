// Map colors and MapLibre paint expressions.
//
// The zoning view uses only three categorical colors plus neutral grays. On a
// map any two colors can sit side by side, and three is the most that stay
// distinguishable for colorblind viewers (checked with the data-viz palette
// validator, all-pairs, in light and dark mode). The legend lets you isolate
// any one of the ten zoning families, and hovering names the exact code.

import type { ExpressionSpecification } from "maplibre-gl";
import type { ColorMode, FamilyCode, Theme } from "./types";

export const BASEMAP: Record<Theme, string> = {
  light: "https://tiles.openfreemap.org/styles/positron",
  dark: "https://tiles.openfreemap.org/styles/dark",
};

export interface ColorGroup {
  id: string;
  label: string;
  families: FamilyCode[];
  neutral: boolean;
  color: Record<Theme, string>;
}

export const COLOR_GROUPS: ColorGroup[] = [
  {
    id: "growth",
    label: "Mixed use & multifamily",
    families: ["mixed_use", "multifamily"],
    neutral: false,
    color: { light: "#2a78d6", dark: "#3987e5" },
  },
  {
    id: "employment",
    label: "Commercial & employment",
    families: ["commercial", "office_rd", "industrial"],
    neutral: false,
    color: { light: "#eb6834", dark: "#d95926" },
  },
  {
    id: "pd",
    label: "Planned development",
    families: ["planned_dev"],
    neutral: false,
    color: { light: "#1baf7a", dark: "#199e70" },
  },
  {
    id: "lowres",
    label: "Single-family & duplex",
    families: ["single_family", "low_density_res"],
    neutral: true,
    color: { light: "#d3d1c9", dark: "#3a3936" },
  },
  {
    id: "public",
    label: "Public / open space",
    families: ["public_open"],
    neutral: true,
    color: { light: "#a3a199", dark: "#5e5d57" },
  },
  {
    id: "none",
    label: "No zoning in City GIS",
    families: ["none"],
    neutral: true,
    color: { light: "rgba(0,0,0,0)", dark: "rgba(0,0,0,0)" },
  },
];

const GROUP_BY_FAMILY = new Map<FamilyCode, ColorGroup>(
  COLOR_GROUPS.flatMap((g) => g.families.map((f) => [f, g] as const)),
);

export const groupFor = (family: FamilyCode) => GROUP_BY_FAMILY.get(family)!;

/** Highlight color for parcels inside a plan area in "plans" mode (categorical slot 1). */
const PLAN_COLOR: Record<Theme, string> = { light: "#2a78d6", dark: "#3987e5" };
const MUTED: Record<Theme, string> = { light: "#dddcd6", dark: "#2c2c2a" };

export const INK: Record<Theme, { outline: string; selected: string; halo: string; plan: string }> = {
  light: { outline: "rgba(40,40,38,0.32)", selected: "#0b0b0b", halo: "#ffffff", plan: "#2b2b29" },
  dark: { outline: "rgba(255,255,255,0.16)", selected: "#ffffff", halo: "#000000", plan: "#e6e5df" },
};

export function fillColor(theme: Theme, mode: ColorMode, isolated: FamilyCode | null): ExpressionSpecification {
  if (mode === "plans") {
    return ["case", ["!=", ["get", "sp"], ""], PLAN_COLOR[theme], MUTED[theme]];
  }
  if (isolated) {
    return ["case", ["==", ["get", "f"], isolated], groupFor(isolated).color[theme], MUTED[theme]];
  }
  const pairs = COLOR_GROUPS.flatMap((g) => g.families.flatMap((f) => [f, g.color[theme]]));
  return ["match", ["get", "f"], ...pairs, MUTED[theme]] as unknown as ExpressionSpecification;
}

export function fillOpacity(mode: ColorMode, isolated: FamilyCode | null): ExpressionSpecification | number {
  if (mode === "plans") return ["case", ["!=", ["get", "sp"], ""], 0.7, 0.35];
  if (isolated) return ["case", ["==", ["get", "f"], isolated], 0.8, 0.3];
  return 0.72;
}
