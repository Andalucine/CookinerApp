/** Recuperar contraseña: 1) email → code sent, 2) 6-digit code + new password. */
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as auth from "../../services/auth.ts";
import { errorText } from "../../services/errors.ts";
import { checkCode, checkEmail, checkPassword } from "../../services/validation.ts";

export default function ForgotPassword() {
  const { t, language } = useI18n();
  const [step, setStep] = useState<"email" | "code" | "done">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [message, setMessage] = useState<{ text: string; kind: "error" | "ok" } | null>(null);
  const [busy, setBusy] = useState(false);

  async function sendCode() {
    const emailError = checkEmail(email);
    setErrors({ email: emailError ? t(emailError) : undefined });
    if (emailError) return;
    setBusy(true);
    try {
      const result = await auth.forgotPassword(email, language);
      setMessage({ text: result.message, kind: "ok" });
      setStep("code");
    } catch (error) {
      setMessage({ text: errorText(error, t), kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    const codeError = checkCode(code);
    const passwordError = checkPassword(password);
    setErrors({
      code: codeError ? t(codeError) : undefined,
      password: passwordError ? t(passwordError) : undefined,
    });
    if (codeError || passwordError) return;
    setBusy(true);
    try {
      await auth.resetPassword(email, code, password, language);
      setMessage({ text: t("forgot.done"), kind: "ok" });
      setStep("done");
    } catch (error) {
      setMessage({ text: errorText(error, t), kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>{t("forgot.title")}</Text>
      {step === "email" ? <Text style={styles.intro}>{t("forgot.intro")}</Text> : null}
      <Message text={message?.text ?? null} kind={message?.kind} />
      {step === "email" ? (
        <>
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
          <BigButton label={t("forgot.send")} onPress={sendCode} loading={busy} />
        </>
      ) : null}
      {step === "code" ? (
        <>
          <TextField
            label={t("forgot.code")}
            value={code}
            onChangeText={setCode}
            error={errors.code}
            keyboardType="number-pad"
            maxLength={6}
            textContentType="oneTimeCode"
            autoComplete="one-time-code"
          />
          <TextField
            label={t("forgot.newPassword")}
            hint={t("register.passwordHint")}
            value={password}
            onChangeText={setPassword}
            error={errors.password}
            password
            autoComplete="new-password"
            textContentType="newPassword"
          />
          <BigButton label={t("forgot.save")} onPress={save} loading={busy} />
        </>
      ) : null}
      <BigButton
        label={t("forgot.back")}
        variant={step === "done" ? "primary" : "link"}
        onPress={() => router.back()}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  intro: { fontSize: fontSize.body, color: colors.muted },
});
