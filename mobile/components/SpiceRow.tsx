/** One spice in a list: name (in the person's language), aliases in small, and its marks in
 * orange circles: a leaf when it has substitutes, layers when it is a blend (the legend on the
 * Especias screen explains them). Tapping opens its card. */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import type { SpiceSummary } from "../services/spices.ts";
import { IconCircle, MARK_BLEND, MARK_SUBSTITUTES } from "./SpiceIcons.tsx";
import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function spiceName(spice: { name: string; name_en: string | null }, language: string) {
  return cap((language === "en" && spice.name_en) || spice.name);
}

export function SpiceRow({ spice }: { spice: SpiceSummary }) {
  const { t, language } = useI18n();
  const name = spiceName(spice, language);
  const marks = [
    spice.has_substitutions ? t("spices.legendSubstitutes") : null,
    spice.is_blend ? t("spices.legendBlend") : null,
  ].filter(Boolean);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={[name, ...marks].join(", ")}
      onPress={() => router.push(`/spices/${spice.id}`)}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
    >
      <View style={styles.text}>
        <Text style={styles.name}>{name}</Text>
        {spice.notebook_blend_id !== null || spice.notebook_spice_id !== null ? (
          <Text style={styles.own} numberOfLines={1}>
            {spice.added_by
              ? t("recipes.addedBy", { name: spice.added_by })
              : spice.notebook_spice_id !== null
                ? t("ownSpice.mark")
                : t(spice.is_own_version ? "blend.markVersion" : "blend.markOwn")}
          </Text>
        ) : spice.aliases ? (
          <Text style={styles.aliases} numberOfLines={1}>
            {spice.aliases}
          </Text>
        ) : null}
      </View>
      {spice.has_substitutions ? <IconCircle name={MARK_SUBSTITUTES} size={36} /> : null}
      {spice.is_blend ? <IconCircle name={MARK_BLEND} size={36} /> : null}
      <Ionicons name="chevron-forward" size={24} color={colors.ink} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: touchHeight + 8,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  pressed: { opacity: 0.7 },
  text: { flex: 1, gap: 2 },
  name: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  aliases: { fontSize: fontSize.small, color: colors.muted },
  own: { fontSize: fontSize.small, fontWeight: "600", color: colors.muted },
});
