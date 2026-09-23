/** A visible message box for errors and confirmations (also read out by VoiceOver). */
import { StyleSheet, Text, View } from "react-native";

import { colors, fontSize, radius, spacing } from "./theme.ts";

export function Message({ text, kind = "error" }: { text: string | null; kind?: "error" | "ok" }) {
  if (!text) return null;
  return (
    <View
      style={[styles.box, kind === "ok" ? styles.ok : styles.error]}
      accessibilityLiveRegion="polite"
      accessibilityRole="alert"
    >
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { padding: spacing.m, borderRadius: radius.m, borderWidth: 2 },
  error: { borderColor: colors.error, backgroundColor: "#FDECEA" },
  ok: { borderColor: colors.success, backgroundColor: "#E7F4EA" },
  text: { fontSize: fontSize.body, color: colors.ink },
});
