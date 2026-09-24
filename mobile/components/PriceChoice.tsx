/**
 * Price of a wine (session 8): "Cualquiera" across, the four symbols € €€ €€€ €€€€ in one row
 * (they are what is searched by), and the same four bands written in euros in two columns.
 * Tapping a symbol or its band selects the same value.
 */
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { PRICE_BANDS } from "../services/wineQuery.ts";
import { chipStyles } from "./Chips.tsx";
import { colors, fontSize, spacing } from "./theme.ts";

export function PriceChoice({
  value,
  onChange,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  const { t } = useI18n();
  const chip = (code: string, text: string, extra: object, big = false) => {
    const selected = value === code;
    return (
      <Pressable
        key={`${code}-${big}`}
        accessibilityRole="radio"
        accessibilityState={{ selected }}
        accessibilityLabel={text}
        onPress={() => onChange(code)}
        style={({ pressed }) => [
          chipStyles.chip,
          extra,
          selected && styles.selected,
          pressed && styles.pressed,
        ]}
      >
        <Text style={[big ? styles.symbol : styles.text, selected && styles.selectedText]}>
          {text}
        </Text>
      </Pressable>
    );
  };
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <View style={chipStyles.grid} accessibilityRole="radiogroup" accessibilityLabel={label}>
        {chip("", t("search.any"), chipStyles.wide)}
        {PRICE_BANDS.map((b) => chip(b.code, b.code, styles.quarter, true))}
        {PRICE_BANDS.map((b) => chip(b.code, t(b.key), chipStyles.half))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  // Four in one row: same base, they grow together
  quarter: { flexBasis: "18%", flexGrow: 1, paddingHorizontal: spacing.xs },
  text: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink, textAlign: "center" },
  symbol: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  selected: { borderColor: colors.ink, backgroundColor: colors.accent },
  selectedText: { color: colors.ink },
  pressed: { opacity: 0.7 },
});
