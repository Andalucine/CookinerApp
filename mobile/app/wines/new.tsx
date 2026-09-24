/** Nuevo vino: by hand, or imported from a shop or winery page (session 8). */
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";

export default function NewWine() {
  const { t } = useI18n();
  return (
    <Screen>
      <Text style={styles.intro}>{t("wines.newIntro")}</Text>
      <View style={styles.buttons}>
        <BigButton
          label={t("new.write")}
          icon="create-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.replace("/wines/write")}
        />
        <BigButton
          label={t("new.web")}
          icon="globe-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.replace("/wines/import")}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  buttons: { gap: spacing.m },
});
