/** One spice in a list: name (in the person's language), aliases in small, a leaf when it has
 * substitutes and the "mezcla" mark. Tapping opens its card. */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import type { SpiceSummary } from "../services/spices.ts";
import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function spiceName(spice: { name: string; name_en: string | null }, language: string) {
  return cap((language === "en" && spice.name_en) || spice.name);
}

export function SpiceRow({ spice }: { spice: SpiceSummary }) {
  const { t, language } = useI18n();
  const name = spiceName(spice, language);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={name}
      onPress={() => router.push(`/spices/${spice.id}`)}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
    >
      <View style={styles.text}>
        <Text style={styles.name}>
          {name}
          {spice.is_blend ? <Text style={styles.blend}>  {t("spices.blendMark")}</Text> : null}
        </Text>
        {spice.aliases ? (
          <Text style={styles.aliases} numberOfLines={1}>
            {spice.aliases}
          </Text>
        ) : null}
      </View>
      {spice.has_substitutions ? <Ionicons name="leaf" size={20} color={colors.ink} /> : null}
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
  blend: { fontSize: fontSize.small, fontWeight: "600", color: colors.muted },
  aliases: { fontSize: fontSize.small, color: colors.muted },
});
