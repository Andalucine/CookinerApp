/** A field to add things one after another (pantry, shopping list), session 9: write, press
 * the big + (or "done" on the keyboard) and the field is empty and ready for the next one. */
import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import { useI18n } from "../i18n";
import { TextField } from "./TextField.tsx";
import { colors, radius, spacing, touchHeight } from "./theme.ts";

export function AddField({
  label,
  hint,
  onAdd,
}: {
  label: string;
  hint?: string;
  onAdd: (text: string) => Promise<void>;
}) {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function add() {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      await onAdd(text);
      setText("");
    } catch {
      // the screen shows what went wrong; the text stays to try again
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.row}>
      <View style={styles.field}>
        <TextField
          label={label}
          hint={hint}
          value={text}
          onChangeText={setText}
          onSubmitEditing={add}
          returnKeyType="done"
          submitBehavior="submit"
          autoCapitalize="none"
        />
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${t("kitchen.add")}: ${label}`}
        onPress={add}
        disabled={busy}
        style={({ pressed }) => [styles.button, pressed && styles.pressed]}
      >
        {busy ? (
          <ActivityIndicator color={colors.ink} />
        ) : (
          <Ionicons name="add" size={32} color={colors.ink} />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-start", gap: spacing.s },
  field: { flex: 1 },
  // lined up with the input box, below the label
  button: {
    marginTop: 30,
    width: touchHeight,
    height: touchHeight,
    borderRadius: radius.m,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: { opacity: 0.7 },
});
