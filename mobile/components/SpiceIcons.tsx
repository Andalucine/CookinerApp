/**
 * The pictures of the spice zone (session 8): an icon for each family, the two marks a spice
 * can carry (leaf = it has substitutes, layers = it is a blend) and the icon of each
 * equivalence rule, always inside the orange circle of the app.
 */
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { StyleSheet, View } from "react-native";

import { colors } from "./theme.ts";

export type IconName = ComponentProps<typeof Ionicons>["name"];

export const FAMILY_ICONS: Record<string, IconName> = {
  herbs: "leaf-outline",
  seeds: "ellipse-outline",
  barks_roots_flowers: "flower-outline",
  peppers_chillies: "flame-outline",
  paprikas: "sunny-outline",
  blends: "layers-outline",
  salts_seasonings: "cube-outline",
};

export const MARK_SUBSTITUTES: IconName = "leaf";
export const MARK_BLEND: IconName = "layers";

/** The icon of a rule, chosen from words of its Spanish title (stable in the catalogue). */
export function ruleIcon(situationEs: string): IconName {
  const s = situationEs.toLowerCase();
  if (s.includes("hierba")) return "leaf-outline";
  if (s.includes("entera")) return "ellipse-outline";
  if (s.includes("guindilla")) return "flame-outline";
  if (s.includes("medida")) return "beaker-outline";
  if (s.includes("jengibre")) return "nutrition-outline";
  if (s.includes("ajo") || s.includes("cebolla")) return "nutrition-outline";
  return "swap-horizontal-outline";
}

export function IconCircle({ name, size = 40 }: { name: IconName; size?: number }) {
  return (
    <View style={[styles.circle, { width: size, height: size, borderRadius: size / 2 }]}>
      <Ionicons name={name} size={Math.round(size * 0.55)} color={colors.ink} />
    </View>
  );
}

const styles = StyleSheet.create({
  circle: { backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" },
});
