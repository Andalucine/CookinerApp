/**
 * What a note is about (session 9): six yellow squares with their icon and name, three per
 * row, above the title. One or none can be chosen; tapping the chosen one again removes it.
 */
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { NOTE_KINDS, toggleKind } from "../services/noteKinds.ts";
import type { NoteKind } from "../services/notes.ts";
import { NoteKindIcon } from "./NoteKindIcon.tsx";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function NoteKindPicker({
  value,
  onChange,
}: {
  value: NoteKind | null;
  onChange: (kind: NoteKind | null) => void;
}) {
  const { t } = useI18n();
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{t("notes.kind")}</Text>
      <View style={styles.grid}>
        {NOTE_KINDS.map((kind) => {
          const on = value === kind.code;
          return (
            <Pressable
              key={kind.code}
              accessibilityRole="radio"
              accessibilityState={{ checked: on }}
              accessibilityLabel={t(kind.label)}
              onPress={() => onChange(toggleKind(value, kind.code))}
              style={({ pressed }) => [styles.tile, on && styles.on, pressed && styles.pressed]}
            >
              <NoteKindIcon kind={kind.code} size={52} />
              <Text style={[styles.name, on && styles.onName]} numberOfLines={1}>
                {t(kind.label)}
              </Text>
              {on ? (
                <View style={styles.check}>
                  <Ionicons name="checkmark" size={18} color={colors.background} />
                </View>
              ) : null}
            </Pressable>
          );
        })}
      </View>
      <Text style={styles.hint}>{t("notes.kindHint")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  tile: {
    flexBasis: "30%",
    flexGrow: 1,
    alignItems: "center",
    gap: spacing.xs,
    paddingVertical: spacing.s,
    paddingHorizontal: spacing.xs,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  on: { borderWidth: 3, borderColor: colors.ink, backgroundColor: colors.accentSoft },
  pressed: { opacity: 0.7 },
  name: { fontSize: fontSize.small, color: colors.ink },
  onName: { fontWeight: "700" },
  check: {
    position: "absolute",
    top: 6,
    right: 6,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.ink,
    alignItems: "center",
    justifyContent: "center",
  },
  hint: { fontSize: fontSize.small, color: colors.muted },
});
