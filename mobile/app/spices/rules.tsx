/** Reglas de equivalencia: the general rules of the spice zone (fresh → dried 3:1, whole →
 * ground…), one card each: the situation, the equivalence in big and a note. */
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Screen } from "../../components/Screen.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

export default function RulesScreen() {
  const { t, language } = useI18n();
  const en = language === "en";
  const data = useLoad(() => spices.rules(language), [language]);

  return (
    <Screen>
      <Text style={styles.intro}>{t("spices.rulesIntro")}</Text>
      {data.loading && !data.data ? (
        <Loading />
      ) : data.error || !data.data ? (
        <LoadError error={data.error} onRetry={data.reload} />
      ) : (
        <View style={styles.list}>
          {data.data.map((rule) => {
            const note = en ? rule.note_en : rule.note_es;
            return (
              <View key={rule.id} style={styles.card}>
                <Text style={styles.situation}>{en ? rule.situation_en : rule.situation_es}</Text>
                <Text style={styles.equivalence}>
                  {en ? rule.equivalence_en : rule.equivalence_es}
                </Text>
                {note ? <Text style={styles.note}>{note}</Text> : null}
              </View>
            );
          })}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  card: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  situation: { fontSize: fontSize.small, fontWeight: "600", color: colors.muted },
  equivalence: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink, lineHeight: 26 },
  note: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
});
