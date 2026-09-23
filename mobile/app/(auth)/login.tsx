/** Bienvenida / Entrar: email, password with "ver", links to create account and recover. */
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Logo } from "../../components/Logo.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as auth from "../../services/auth.ts";
import { errorText } from "../../services/errors.ts";
import { useSession } from "../../services/session.tsx";
import { checkEmail, checkRequired } from "../../services/validation.ts";

export default function Login() {
  const { t, language } = useI18n();
  const { signIn } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    const emailError = checkEmail(email);
    const passwordError = checkRequired(password);
    setErrors({
      email: emailError ? t(emailError) : undefined,
      password: passwordError ? t(passwordError) : undefined,
    });
    setMessage(null);
    if (emailError || passwordError) return;
    setBusy(true);
    try {
      const result = await auth.login(email, password, language);
      await signIn(result.access_token, result.user);
      router.replace("/");
    } catch (error) {
      setMessage(errorText(error, t));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen centered>
      <Logo size={200} />
      <Text style={styles.title}>{t("login.title")}</Text>
      <Message text={message} />
      <TextField
        label={t("login.email")}
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        textContentType="emailAddress"
        returnKeyType="next"
      />
      <TextField
        label={t("login.password")}
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        password
        autoComplete="current-password"
        textContentType="password"
        returnKeyType="go"
        onSubmitEditing={submit}
      />
      <BigButton label={t("login.submit")} onPress={submit} loading={busy} icon="log-in-outline" />
      <BigButton
        label={t("login.forgot")}
        variant="link"
        onPress={() => router.push("/forgot-password")}
      />
      <View style={styles.separator} />
      <Text style={styles.question}>{t("login.noAccount")}</Text>
      <BigButton
        label={t("login.createAccount")}
        variant="secondary"
        onPress={() => router.push("/register")}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink, textAlign: "center" },
  separator: { height: 1, backgroundColor: colors.border, marginVertical: spacing.s },
  question: { fontSize: fontSize.body, color: colors.muted, textAlign: "center" },
});
