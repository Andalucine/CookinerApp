/** One note in the list: the yellow square of its kind in front (session 9), title, the start
 * of its text and the day it was last changed. */
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import type { NoteSummary } from "../services/notes.ts";
import { kindLabel } from "../services/noteKinds.ts";
import { shortDate } from "../services/sharedNotebook.ts";
import { NoteKindIcon } from "./NoteKindIcon.tsx";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function NoteCard({ note, onPress }: { note: NoteSummary; onPress: () => void }) {
  const { t, language } = useI18n();
  const changed = t("notes.changed", { date: shortDate(note.updated_at, language) });
  const by = note.added_by ? t("recipes.addedBy", { name: note.added_by }) : null;
  const kind = kindLabel(note.kind);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={[kind ? t(kind) : null, note.title, note.preview, changed, by].filter(Boolean).join(", ")}
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <NoteKindIcon kind={note.kind} size={48} />
      <View style={styles.text}>
        <Text style={styles.title}>{note.title}</Text>
        {note.preview && note.preview !== note.title ? (
          <Text style={styles.preview} numberOfLines={2}>
            {note.preview}
          </Text>
        ) : null}
        <Text style={styles.details}>{[changed, by].filter(Boolean).join(" · ")}</Text>
      </View>
      <Ionicons name="chevron-forward" size={24} color={colors.ink} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.m,
    minHeight: 72,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  pressed: { opacity: 0.7 },
  text: { flex: 1, gap: 4 },
  title: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  preview: { fontSize: fontSize.small, color: colors.ink },
  details: { fontSize: fontSize.small, color: colors.muted },
});
