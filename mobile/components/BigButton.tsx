/**
 * The main button: big, high contrast. Optional icon, optionally inside the orange circle
 * (like the five doors), and a "column" layout (circle above the text) for half-width buttons.
 */
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

type Props = {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "link";
  icon?: ComponentProps<typeof Ionicons>["name"];
  iconCircle?: boolean; // icon inside the orange circle
  layout?: "row" | "column";
  fill?: boolean; // take all the height of its row (for buttons side by side)
  loading?: boolean;
  disabled?: boolean;
};

export const ICON_CIRCLE = 44;

export function BigButton({
  label,
  onPress,
  variant = "primary",
  icon,
  iconCircle,
  layout = "row",
  fill,
  loading,
  disabled,
}: Props) {
  const off = disabled || loading;
  const iconView = icon ? (
    iconCircle ? (
      <View style={styles.circle}>
        <Ionicons name={icon} size={24} color={colors.ink} />
      </View>
    ) : (
      <Ionicons name={icon} size={24} color={colors.ink} />
    )
  ) : null;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!off, busy: !!loading }}
      onPress={onPress}
      disabled={off}
      style={({ pressed }) => [
        styles.base,
        layout === "column" && styles.column,
        fill && styles.fill,
        variant === "primary" && styles.primary,
        variant === "secondary" && styles.secondary,
        variant === "link" && styles.link,
        pressed && styles.pressed,
        off && styles.disabled,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.ink} />
      ) : (
        <>
          {iconView}
          <Text
            style={[styles.label, variant === "link" && styles.linkLabel]}
            numberOfLines={layout === "column" ? 3 : 2}
          >
            {label}
          </Text>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: touchHeight,
    borderRadius: radius.m,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.s,
  },
  column: { flexDirection: "column", paddingVertical: spacing.m, minHeight: 128 },
  fill: { flexGrow: 1 },
  primary: { backgroundColor: colors.accent },
  secondary: { backgroundColor: colors.background, borderWidth: 2, borderColor: colors.ink },
  link: { minHeight: 48 },
  pressed: { opacity: 0.7 },
  disabled: { opacity: 0.5 },
  circle: {
    width: ICON_CIRCLE,
    height: ICON_CIRCLE,
    borderRadius: ICON_CIRCLE / 2,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontSize: fontSize.body,
    fontWeight: "700",
    color: colors.ink,
    textAlign: "center",
    flexShrink: 1,
  },
  linkLabel: { fontWeight: "600", textDecorationLine: "underline" },
});
