/** The wine section belongs to the paid plans (bible, session 5). On the free plan the door
 * opens on an explanation instead (decided in session 8). */
import { StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import type { User } from "../services/auth.ts";
import { Screen } from "./Screen.tsx";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function winesAllowed(user: User): boolean {
  return user.plan !== "free";
}

export function WinesNotInPlan() {
  const { t } = useI18n();
  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.title}>{t("wines.freeTitle")}</Text>
        <Text style={styles.body}>{t("wines.freeText")}</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.s, padding: spacing.m, borderRadius: radius.m, backgroundColor: colors.surface },
  title: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
});
