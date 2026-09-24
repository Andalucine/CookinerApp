/**
 * Mi cuenta: account data, the language of the app (saved in the account, session 8), the
 * notebooks shared with me (each one opens its Recetas) and sign out.
 */
import Constants from "expo-constants";
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { isLanguage, LANGUAGES } from "../../i18n/translate.ts";
import { errorText } from "../../services/errors.ts";
import * as notebooks from "../../services/notebooks.ts";
import { useSession } from "../../services/session.tsx";
import { notebookParams } from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function Settings({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const { user } = auth;
  const { signOut, updateUser } = useSession();
  const shared = useLoad(() => notebooks.sharedWithMe(auth), [auth.token, auth.language]);
  const [languageError, setLanguageError] = useState<string | null>(null);

  async function changeLanguage(language: string) {
    if (!isLanguage(language)) return;
    if (language === user.language) return;
    setLanguageError(null);
    try {
      updateUser(await notebooks.setLanguage(auth, language));
    } catch (error) {
      setLanguageError(errorText(error, t));
    }
  }

  async function logout() {
    await signOut();
    router.replace("/login");
  }

  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.name}>{user.display_name}</Text>
        <Text style={styles.detail}>{user.email}</Text>
        <Text style={styles.detail}>
          {t("home.plan", { plan: t(`plan.${user.plan}` as TextKey) })}
        </Text>
      </View>

      <Chips
        label={t("settings.language")}
        value={user.language}
        onChange={changeLanguage}
        options={LANGUAGES.map((l) => ({ value: l.code, label: l.label }))}
      />
      <Message text={languageError} />

      <SectionTitle text={t("settings.sharedWithMe")} />
      {shared.loading && !shared.data ? (
        <Loading />
      ) : shared.error || !shared.data ? (
        <LoadError error={shared.error} onRetry={shared.reload} />
      ) : shared.data.length === 0 ? (
        <Text style={styles.detail}>{t("settings.sharedNone")}</Text>
      ) : (
        <View style={styles.list}>
          {shared.data.map((notebook) => (
            <RowButton
              key={notebook.id}
              icon="people-outline"
              label={t("shared.notebookRole", {
                name: notebook.owner.display_name,
                role: t(notebook.role === "editor" ? "role.editor" : "role.viewer"),
              })}
              onPress={() =>
                router.push({
                  pathname: "/recipes",
                  params: notebookParams({
                    id: notebook.id,
                    owner: notebook.owner.display_name,
                    role: notebook.role,
                  }),
                })
              }
            />
          ))}
        </View>
      )}

      <View style={styles.logout}>
        <BigButton
          label={t("settings.logout")}
          icon="log-out-outline"
          variant="secondary"
          onPress={logout}
        />
      </View>
      <Text style={styles.version}>
        {t("settings.version", { version: Constants.expoConfig?.version ?? "" })}
      </Text>
    </Screen>
  );
}

export default function SettingsScreen() {
  return <SignedIn>{(auth) => <Settings auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  card: {
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
    gap: spacing.xs,
  },
  name: { fontSize: fontSize.large, fontWeight: "700", color: colors.ink },
  detail: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  logout: { marginTop: spacing.l },
  version: { fontSize: fontSize.small, color: colors.muted, textAlign: "center", marginTop: spacing.l },
});
