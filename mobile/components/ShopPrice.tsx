/**
 * Buy the wine in the shop (session 9: CookinerApp is Vinoselección's sales agent). One row:
 * the orange button "Comprar en Vinoselección", which opens its page with the agent's code
 * (`shop_url`), and the price there. When the shop has sold out, a grey notice instead.
 */
import { Ionicons } from "@expo/vector-icons";
import * as WebBrowser from "expo-web-browser";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { formatPrice } from "../services/wineQuery.ts";
import type { WineSummary } from "../services/wines.ts";
import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

type Props = { wine: Pick<WineSummary, "shop_url" | "source_name" | "source_price" | "in_stock"> };

export function ShopPrice({ wine }: Props) {
  const { t, language } = useI18n();
  const shop = wine.source_name || "Vinoselección";
  const price = formatPrice(wine.source_price, language);
  if (!wine.in_stock) {
    return (
      <View style={styles.soldOut}>
        <Ionicons name="alert-circle-outline" size={22} color={colors.muted} />
        <Text style={styles.soldOutText}>{t("wines.soldOutText", { shop })}</Text>
      </View>
    );
  }
  return (
    <View style={styles.row}>
      <Pressable
        accessibilityRole="link"
        accessibilityLabel={t("wines.buyAt", { shop })}
        onPress={() => WebBrowser.openBrowserAsync(wine.shop_url)}
        style={({ pressed }) => [styles.buy, pressed && styles.pressed]}
      >
        <Ionicons name="cart-outline" size={24} color={colors.ink} />
        <Text style={styles.buyText}>{t("wines.buyAt", { shop })}</Text>
        <Ionicons name="open-outline" size={18} color={colors.ink} />
      </Pressable>
      {price ? (
        <View style={styles.price} accessibilityLabel={t("wines.shopPrice", { price })}>
          <Text style={styles.priceText}>{price}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.s },
  buy: {
    flex: 1,
    minHeight: touchHeight,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    paddingHorizontal: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.accent,
  },
  buyText: { flex: 1, fontSize: fontSize.body, fontWeight: "800", color: colors.ink },
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
  soldOut: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  soldOutText: { flex: 1, fontSize: fontSize.body, color: colors.muted },
  pressed: { opacity: 0.7 },
});
