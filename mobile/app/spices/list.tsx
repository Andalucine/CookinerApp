/** The spices of one family (Hierbas aromáticas, Mezclas…), each one opening its card. */
import { Stack, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SpiceRow } from "../../components/SpiceRow.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

export default function SpiceListScreen() {
  const { family, title } = useLocalSearchParams<{ family?: string; title?: string }>();
  const { t, language } = useI18n();
  const data = useLoad(() => spices.list(language, { family }), [language, family]);

  return (
    <Screen>
      <Stack.Screen options={{ title: title || t("home.spices") }} />
      {data.loading && !data.data ? (
        <Loading />
      ) : data.error || !data.data ? (
        <LoadError error={data.error} onRetry={data.reload} />
      ) : (
        <>
          <Text style={styles.muted}>
            {family === "blends" ? t("spices.blendsHint") : t("spices.listHint")}
          </Text>
          <View style={styles.list}>
            {data.data.map((spice) => (
              <SpiceRow key={spice.id} spice={spice} />
            ))}
          </View>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  muted: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
});
