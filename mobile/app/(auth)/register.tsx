/** Crear cuenta: name, email, password and language. The notebook is created by the API. */
import { router } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing, touchHeight } from "../../components/theme.ts";
import { type Language, useI18n } from "../../i18n";
import * as auth from "../../services/auth.ts";
import { errorText } from "../../services/errors.ts";
import { useSession } from "../../services/session.tsx";
import { checkEmail, checkPassword, checkRequired } from "../../services/validation.ts";

const LANGUAGES: { code: Language; label: string }[] = [
  { code: "es", label: "Español" },
  { code: "en", label: "English" },
];

export default function Register() {
  const { t, language, setLanguage } = useI18n();
  const { signIn } = useSession();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    const found = {
      name: checkRequired(name),
      email: checkEmail(email),
      password: checkPassword(password),
    };
    setErrors(
      Object.fromEntries(Object.entries(found).map(([k, v]) => [k, v ? t(v) : undefined])),
    );
    setMessage(null);
    if (Object.values(found).some(Boolean)) return;
    setBusy(true);
    try {
      const result = await auth.register(email, name, password, language);
      await signIn(result.access_token, result.user);
      router.replace("/");
    } catch (error) {
      setMessage(errorText(error, t));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>{t("register.title")}</Text>
      <Message text={message} />
      <TextField
        label={t("register.name")}
        hint={t("register.nameHint")}
        value={name}
        onChangeText={setName}
        error={errors.name}
        autoComplete="name"
        textContentType="name"
      />
      <TextField
        label={t("login.email")}
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        textContentType="emailAddress"
      />
      <TextField
        label={t("login.password")}
        hint={t("register.passwordHint")}
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        password
        autoComplete="new-password"
        textContentType="newPassword"
      />
      <Text style={styles.label}>{t("register.language")}</Text>
      <View style={styles.row} accessibilityRole="radiogroup">
        {LANGUAGES.map((option) => {
          const selected = option.code === language;
          return (
            <Pressable
              key={option.code}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              onPress={() => setLanguage(option.code)}
              style={[styles.choice, selected && styles.choiceSelected]}
            >
              <Text style={styles.choiceText}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>
      <BigButton label={t("register.submit")} onPress={submit} loading={busy} />
      <BigButton label={t("register.haveAccount")} variant="link" onPress={() => router.back()} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  row: { flexDirection: "row", gap: spacing.m },
  choice: {
    flex: 1,
    minHeight: touchHeight,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  choiceSelected: { borderColor: colors.ink, backgroundColor: colors.accentSoft },
  choiceText: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
});
