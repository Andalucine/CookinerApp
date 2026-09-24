/** Big choices where several can be on at once (seasons, occasions of a recipe), in the same
 * grid of two equal columns as Chips (rule of the app, session 7). */
import { Pressable, StyleSheet, Text, View } from "react-native";

import { chipStyles } from "./Chips.tsx";
import { wideFlags } from "./gridLayout.ts";
import { colors, fontSize, spacing } from "./theme.ts";

export function ToggleChips({
  label,
  options,
  selected,
  onToggle,
  anyLabel,
  onClear,
  perRow = 2,
}: {
  label: string;
  options: { value: number; label: string; wide?: boolean }[];
  selected: number[];
  onToggle: (value: number) => void;
  anyLabel?: string; // "Cualquiera": on when nothing is marked; tapping it clears the rest
  onClear?: () => void;
  perRow?: 2 | 3; // 3: a single row of three (Beatriz, session 9: the meals of the menu)
}) {
  const wide = perRow === 3 ? options.map(() => false) : wideFlags(options);
  const none = selected.length === 0;
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <View style={chipStyles.grid}>
        {anyLabel && onClear ? (
          <Pressable
            accessibilityRole="checkbox"
            accessibilityState={{ checked: none }}
            accessibilityLabel={anyLabel}
            onPress={onClear}
            style={({ pressed }) => [
              chipStyles.chip,
              chipStyles.wide,
              none && styles.on,
              pressed && styles.pressed,
            ]}
          >
            <Text style={[styles.text, none && styles.onText]}>{anyLabel}</Text>
          </Pressable>
        ) : null}
        {options.map((option, index) => {
          const on = selected.includes(option.value);
          return (
            <Pressable
              key={option.value}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: on }}
              accessibilityLabel={option.label}
              onPress={() => onToggle(option.value)}
              style={({ pressed }) => [
                chipStyles.chip,
                wide[index] ? chipStyles.wide : perRow === 3 ? chipStyles.third : chipStyles.half,
                on && styles.on,
                pressed && styles.pressed,
              ]}
            >
              <Text style={[styles.text, on && styles.onText]}>
                {on ? "✓ " : ""}
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  on: { borderColor: colors.ink, backgroundColor: colors.accent },
  pressed: { opacity: 0.7 },
  text: { fontSize: fontSize.body, color: colors.ink, textAlign: "center" },
  onText: { fontWeight: "700" },
});
