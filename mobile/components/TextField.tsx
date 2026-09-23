/** Labelled text field with its error below. Password fields get the "ver contraseña" eye. */
import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, type TextInputProps, View } from "react-native";

import { useI18n } from "../i18n";
import { colors, fontSize, radius, spacing, touchHeight } from "./theme.ts";

type Props = TextInputProps & {
  label: string;
  hint?: string;
  error?: string | null;
  password?: boolean;
};

export function TextField({ label, hint, error, password, style, ...input }: Props) {
  const { t } = useI18n();
  const [visible, setVisible] = useState(false);
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.box, error ? styles.boxError : null]}>
        <TextInput
          accessibilityLabel={label}
          placeholderTextColor={colors.muted}
          secureTextEntry={password && !visible}
          autoCapitalize={password ? "none" : input.autoCapitalize}
          autoCorrect={password ? false : input.autoCorrect}
          style={[styles.input, style]}
          {...input}
        />
        {password ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={visible ? t("password.hide") : t("password.show")}
            onPress={() => setVisible((v) => !v)}
            hitSlop={12}
            style={styles.eye}
          >
            <Ionicons name={visible ? "eye-off-outline" : "eye-outline"} size={26} color={colors.ink} />
          </Pressable>
        ) : null}
      </View>
      {error ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : hint ? (
        <Text style={styles.hint}>{hint}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  box: {
    minHeight: touchHeight,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: radius.m,
    backgroundColor: colors.background,
  },
  boxError: { borderColor: colors.error },
  input: { flex: 1, fontSize: fontSize.body, color: colors.ink, paddingHorizontal: spacing.m },
  eye: { paddingHorizontal: spacing.m, minHeight: touchHeight, justifyContent: "center" },
  hint: { fontSize: fontSize.small, color: colors.muted },
  error: { fontSize: fontSize.small, color: colors.error, fontWeight: "600" },
});
