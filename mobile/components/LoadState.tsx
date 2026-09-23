/** While a screen loads, and when loading fails (with "Reintentar"). */
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { useI18n } from "../i18n";
import { errorText } from "../services/errors.ts";
import { BigButton } from "./BigButton.tsx";
import { Message } from "./Message.tsx";
import { colors, spacing } from "./theme.ts";

export function Loading() {
  const { t } = useI18n();
  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color={colors.ink} accessibilityLabel={t("common.loading")} />
    </View>
  );
}

export function LoadError({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useI18n();
  return (
    <View style={styles.error}>
      <Message text={errorText(error, t)} />
      <BigButton label={t("common.retry")} icon="refresh" variant="secondary" onPress={onRetry} />
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.l,
    backgroundColor: colors.background,
  },
  error: { gap: spacing.m },
});
