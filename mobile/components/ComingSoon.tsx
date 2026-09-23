/** Placeholder for the sections that arrive in the next sessions. */
import { StyleSheet, Text } from "react-native";

import { useI18n } from "../i18n";
import { Logo } from "./Logo.tsx";
import { Screen } from "./Screen.tsx";
import { colors, fontSize } from "./theme.ts";

export function ComingSoon() {
  const { t } = useI18n();
  return (
    <Screen centered>
      <Logo small size={96} />
      <Text style={styles.title}>{t("soon.title")}</Text>
      <Text style={styles.text}>{t("soon.text")}</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink, textAlign: "center" },
  text: { fontSize: fontSize.body, color: colors.muted, textAlign: "center" },
});
