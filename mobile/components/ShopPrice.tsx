/**
 * Where the wine was seen and at what price (session 8): two cells in one row, a button with
 * the shop's name that opens its page, and a small cell with the price there. Shown only when
 * the page it was imported from published a price.
 */
import { Ionicons } from "@expo/vector-icons";
import * as WebBrowser from "expo-web-browser";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { siteName } from "../services/format.ts";
import { formatPrice } from "../services/wineQuery.ts";
import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

export function ShopPrice({
  sourceUrl,
  sourceName,
  sourcePrice,
}: {
  sourceUrl: string | null;
  sourceName: string | null;
  sourcePrice: number | null;
}) {
  const { t, language } = useI18n();
  const price = formatPrice(sourcePrice, language);
  const name = sourceName || (sourceUrl ? siteName(sourceUrl) : null);
  if (!price || !name) return null;
  return (
    <View style={styles.row}>
      <Pressable
        accessibilityRole="link"
        accessibilityLabel={t("wines.openShop", { shop: name })}
        disabled={!sourceUrl}
        onPress={() => sourceUrl && WebBrowser.openBrowserAsync(sourceUrl)}
        style={({ pressed }) => [styles.shop, pressed && styles.pressed]}
      >
        <Ionicons name="storefront-outline" size={22} color={colors.ink} />
        <Text style={styles.shopText} numberOfLines={1}>
          {name}
        </Text>
        {sourceUrl ? <Ionicons name="open-outline" size={18} color={colors.muted} /> : null}
      </Pressable>
      <View style={styles.price} accessibilityLabel={t("wines.shopPrice", { price })}>
        <Text style={styles.priceText}>{price}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.s },
  shop: {
    flex: 1,
    minHeight: touchHeight,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    paddingHorizontal: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.ink,
    backgroundColor: colors.background,
  },
  shopText: { flex: 1, fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  price: {
    minHeight: touchHeight,
    minWidth: 104,
    paddingHorizontal: spacing.m,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.m,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  priceText: { fontSize: fontSize.body, fontWeight: "800", color: colors.ink },
  pressed: { opacity: 0.7 },
});
