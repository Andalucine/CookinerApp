/**
 * Importar de una web: paste the address → "Leer la página" → the preview, in the same form as
 * writing by hand, to correct what was read badly → Guardar. The link to the source is kept.
 * With someone else's notebook in the parameters (editors), the recipe is saved there.
 */
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Message } from "../../components/Message.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { RecipeForm } from "../../components/RecipeForm.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as imports from "../../services/imports.ts";
import { type OtherNotebook, readNotebook } from "../../services/sharedNotebook.ts";

function Import({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<imports.ImportPreview | null>(null);

  async function read() {
    if (!/^https?:\/\/\S+\.\S+/i.test(url.trim())) {
      setError(t("import.errorUrl"));
      return;
    }
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      setPreview(await imports.readPage(auth, url, notebook?.id));
    } catch (e) {
      setMessage(errorText(e, t));
    } finally {
      setBusy(false);
    }
  }

  if (preview) {
    return (
      <Screen>
        <NotebookBanner notebook={notebook} />
        <View style={styles.check}>
          <Text style={styles.checkTitle}>{t("import.checkTitle")}</Text>
          <Text style={styles.body}>{t("import.checkText")}</Text>
          {preview.warnings.map((w) => (
            <Text key={w} style={styles.warning}>
              • {t(`import.warning.${w}` as TextKey)}
            </Text>
          ))}
        </View>
        <RecipeForm
          auth={auth}
          initial={preview.recipe}
          notebookId={preview.notebook_id}
          sourceLocked
          submitLabel={t("form.save")}
          onSubmit={async (input) => {
            const saved = await imports.save(auth, preview.job_id, input);
            router.replace(`/recipes/${saved.id}`);
          }}
        />
        <BigButton label={t("import.another")} variant="link" onPress={() => setPreview(null)} />
      </Screen>
    );
  }

  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      <Text style={styles.body}>{t("import.intro")}</Text>
      <TextField
        label={t("import.url")}
        hint={t("import.urlHint")}
        value={url}
        onChangeText={setUrl}
        error={error}
        keyboardType="url"
        autoCapitalize="none"
        autoCorrect={false}
        returnKeyType="go"
        onSubmitEditing={read}
      />
      <Message text={message} />
      <BigButton label={t("import.read")} icon="download-outline" loading={busy} onPress={read} />
      {busy ? <Text style={styles.muted}>{t("import.reading")}</Text> : null}
    </Screen>
  );
}

export default function ImportScreen() {
  const notebook = readNotebook(useLocalSearchParams());
  return <SignedIn>{(auth) => <Import auth={auth} notebook={notebook} />}</SignedIn>;
}

const styles = StyleSheet.create({
  body: { fontSize: fontSize.body, color: colors.ink },
  muted: { fontSize: fontSize.small, color: colors.muted, textAlign: "center" },
  check: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.accent,
    backgroundColor: colors.accentSoft,
  },
  checkTitle: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  warning: { fontSize: fontSize.body, color: colors.ink },
});
