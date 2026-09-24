/** One wine in a list: name, winery · D.O. · vintage, its type, the price in the shop (or
 * "Agotado"); star when favourite. */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { localName } from "../services/format.ts";
import { formatPrice, wineDetails } from "../services/wineQuery.ts";
import type { WineSummary } from "../services/wines.ts";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function WineCard({ wine, onPress }: { wine: WineSummary; onPress?: () => void }) {
  const { t, language } = useI18n();
  const details = wineDetails({ ...wine, price_range: null });
  const type = wine.category ? localName(wine.category, language) : null;
  const price = wine.in_stock ? formatPrice(wine.source_price, language) : t("wines.soldOut");
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={[wine.name, details, type, price].filter(Boolean).join(", ")}
      onPress={onPress ?? (() => router.push(`/wines/${wine.id}`))}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.text}>
        <Text style={styles.title}>{wine.name}</Text>
        {details ? <Text style={styles.details}>{details}</Text> : null}
        {type ? <Text style={styles.details}>{type}</Text> : null}
        {price ? (
          <Text style={[styles.price, !wine.in_stock && styles.soldOut]}>{price}</Text>
        ) : null}
      </View>
      {wine.is_favorite ? <Ionicons name="star" size={24} color={colors.accent} /> : null}
      <Ionicons name="chevron-forward" size={24} color={colors.ink} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    minHeight: 72,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  pressed: { opacity: 0.7 },
  text: { flex: 1, gap: 2 },
  title: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  details: { fontSize: fontSize.small, color: colors.muted },
  price: { fontSize: fontSize.small, fontWeight: "800", color: colors.ink },
  soldOut: { color: colors.muted, fontWeight: "600" },
});
