/** The notice on top when the screen shows someone else's notebook: "Cuaderno de Marta" and
 * what I can do in it (session 8). Also "Receta del cuaderno de Marta" on a recipe (session 6). */
import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import type { OtherNotebook } from "../services/sharedNotebook.ts";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function NotebookBanner({
  notebook,
  title,
}: {
  notebook: OtherNotebook | null;
  title?: string; // instead of "Cuaderno de NOMBRE"
}) {
  const { t } = useI18n();
  if (!notebook) return null;
  return (
    <View style={styles.banner} accessibilityRole="summary">
      <Ionicons name="people-outline" size={24} color={colors.ink} />
      <View style={styles.text}>
        <Text style={styles.title}>{title ?? t("shared.notebookOf", { name: notebook.owner })}</Text>
        {title ? null : (
          <Text style={styles.detail}>
            {notebook.role === "editor" ? t("shared.canEdit") : t("shared.canView")}
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  text: { flex: 1, gap: 2 },
  title: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  detail: { fontSize: fontSize.small, color: colors.ink },
});
