/** Nueva receta: the three ways in (a mano · de una web · de YouTube), always to a form that
 * is checked before saving. YouTube as the main source arrives in a later session. */
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";

export default function NewRecipe() {
  const { t } = useI18n();
  return (
    <Screen>
      <Text style={styles.intro}>{t("new.intro")}</Text>
      <View style={styles.buttons}>
        <BigButton
          label={t("new.write")}
          icon="create-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.replace("/recipes/write")}
        />
        <BigButton
          label={t("new.web")}
          icon="globe-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.replace("/recipes/import")}
        />
        <BigButton
          label={t("new.youtube")}
          icon="logo-youtube"
          iconCircle
          variant="secondary"
          disabled
          onPress={() => {}}
        />
        <Text style={styles.soon}>{t("new.youtubeSoon")}</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  buttons: { gap: spacing.m },
  soon: { fontSize: fontSize.small, color: colors.muted, textAlign: "center" },
});
