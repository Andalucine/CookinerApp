/**
 * Big choices where one is selected (time, season, source...), in a grid of two equal columns
 * (rule of the app, session 7). With `allowNone`, tapping the selected one again clears it.
 */
import { Pressable, StyleSheet, Text, View } from "react-native";

import { wideFlags } from "./gridLayout.ts";
import { colors, fontSize, radius, spacing } from "./theme.ts";

type Option = { value: string; label: string; wide?: boolean };

export function Chips({
  options,
  value,
  onChange,
  label,
  allowNone = false,
  hint,
}: {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  label: string;
  allowNone?: boolean;
  hint?: string;
}) {
  const wide = wideFlags(options);
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
      <View style={styles.grid} accessibilityRole="radiogroup" accessibilityLabel={label}>
        {options.map((option, index) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={option.value}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={option.label}
              onPress={() => onChange(selected && allowNone ? "" : option.value)}
              style={({ pressed }) => [
                styles.chip,
                wide[index] ? styles.wide : styles.half,
                selected && styles.selected,
                pressed && styles.pressed,
              ]}
            >
              <Text style={[styles.text, selected && styles.selectedText]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export const chipStyles = StyleSheet.create({
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  chip: {
    minHeight: 52,
    paddingHorizontal: spacing.s,
    paddingVertical: spacing.xs,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  // Two per row of the same width (both grow from the same base), or one across
  half: { flexBasis: "40%", flexGrow: 1 },
  wide: { flexBasis: "100%" },
});

const styles = StyleSheet.create({
  ...chipStyles,
  wrapper: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  hint: { fontSize: fontSize.small, color: colors.muted },
  selected: { borderColor: colors.ink, backgroundColor: colors.accent },
  pressed: { opacity: 0.7 },
  text: { fontSize: fontSize.body, color: colors.ink, textAlign: "center" },
  selectedText: { fontWeight: "700" },
});
