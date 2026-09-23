/** Title of a part of a screen ("Ingredientes", "Pasos"...). */
import { StyleSheet, Text } from "react-native";

import { colors, fontSize, spacing } from "./theme.ts";

export function SectionTitle({ text }: { text: string }) {
  return (
    <Text style={styles.title} accessibilityRole="header">
      {text}
    </Text>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: fontSize.large,
    fontWeight: "800",
    color: colors.ink,
    marginTop: spacing.m,
  },
});
