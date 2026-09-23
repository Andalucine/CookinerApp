/** Common frame of every screen: safe area, white background, scroll and keyboard handling. */
import type { ReactNode } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, spacing } from "./theme.ts";

export function Screen({ children, centered = false }: { children: ReactNode; centered?: boolean }) {
  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom", "left", "right"]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={[styles.content, centered && styles.centered]}
          keyboardShouldPersistTaps="handled"
        >
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
  content: { padding: spacing.l, gap: spacing.m, flexGrow: 1 },
  centered: { justifyContent: "center" },
});
