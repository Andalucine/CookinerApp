/** The yellow square with the icon of what a note is about (session 9). */
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { StyleSheet, View } from "react-native";

import { kindIcon } from "../services/noteKinds.ts";
import type { NoteKind } from "../services/notes.ts";
import { colors } from "./theme.ts";

type IconName = ComponentProps<typeof Ionicons>["name"];

export function NoteKindIcon({ kind, size = 48 }: { kind: NoteKind | null; size?: number }) {
  return (
    <View
      style={[styles.square, { width: size, height: size, borderRadius: Math.round(size / 5) }]}
      accessible={false}
    >
      <Ionicons
        name={kindIcon(kind) as IconName}
        size={Math.round(size * 0.55)}
        color={colors.ink}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  square: { backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" },
});
