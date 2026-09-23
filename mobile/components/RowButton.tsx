/** A full-width row to tap, with an optional number on the right (category tree, links). */
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

export function RowButton({
  label,
  onPress,
  count,
  icon,
  strong,
  muted,
}: {
  label: string;
  onPress: () => void;
  count?: number;
  icon?: ComponentProps<typeof Ionicons>["name"];
  strong?: boolean;
  muted?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={count !== undefined ? `${label}, ${count}` : label}
      onPress={onPress}
      style={({ pressed }) => [styles.row, strong && styles.strong, pressed && styles.pressed]}
    >
      {icon ? (
        <View style={styles.circle}>
          <Ionicons name={icon} size={22} color={colors.ink} />
        </View>
      ) : null}
      <Text style={[styles.label, strong && styles.labelStrong, muted && styles.muted]}>
        {label}
      </Text>
      {count !== undefined ? (
        <Text style={[styles.count, !count && styles.muted]}>{count}</Text>
      ) : null}
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
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  strong: { borderColor: colors.ink, backgroundColor: colors.accentSoft },
  pressed: { opacity: 0.7 },
  circle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  label: { flex: 1, fontSize: fontSize.body, color: colors.ink, paddingVertical: spacing.s },
  labelStrong: { fontWeight: "700" },
  muted: { color: colors.muted },
  count: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
});
