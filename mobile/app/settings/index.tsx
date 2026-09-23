/** Mi cuenta (the settings screen, first version): account data and sign out. Language,
 * password, plan and the notebooks shared with me arrive in a later session. */
import Constants from "expo-constants";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { useSession } from "../../services/session.tsx";

export default function Settings() {
  const { t } = useI18n();
  const { user, signOut } = useSession();

  async function logout() {
    await signOut();
    router.replace("/login");
  }

  return (
    <Screen>
      {user ? (
        <View style={styles.card}>
          <Text style={styles.name}>{user.display_name}</Text>
          <Text style={styles.detail}>{user.email}</Text>
          <Text style={styles.detail}>
            {t("home.plan", { plan: t(`plan.${user.plan}` as TextKey) })}
          </Text>
        </View>
      ) : null}
      <BigButton label={t("settings.logout")} icon="log-out-outline" variant="secondary" onPress={logout} />
      <Text style={styles.version}>
        {t("settings.version", { version: Constants.expoConfig?.version ?? "" })}
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
    gap: spacing.xs,
  },
  name: { fontSize: fontSize.large, fontWeight: "700", color: colors.ink },
  detail: { fontSize: fontSize.body, color: colors.muted },
  version: { fontSize: fontSize.small, color: colors.muted, textAlign: "center", marginTop: spacing.l },
});
