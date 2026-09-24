/**
 * Importar un vino de una web (session 8): paste the address of the wine's page in a shop or
 * winery → "Leer la página" → the preview in the same form as writing by hand → Guardar vino.
 * The link to the page is kept as the source.
 */
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { WineForm } from "../../components/WineForm.tsx";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as wines from "../../services/wines.ts";

function Import({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<wines.WineImportPreview | null>(null);

  async function read() {
    if (!/^https?:\/\/\S+\.\S+/i.test(url.trim())) {
      setError(t("import.errorUrl"));
      return;
    }
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      setPreview(await wines.readPage(auth, url));
    } catch (e) {
      setMessage(errorText(e, t));
    } finally {
      setBusy(false);
    }
  }

  if (preview) {
    const initial = { ...preview.wine, name: preview.wine.name === "?" ? "" : preview.wine.name };
    return (
      <Screen>
        <View style={styles.check}>
          <Text style={styles.checkTitle}>{t("wineImport.checkTitle")}</Text>
          <Text style={styles.body}>{t("wineImport.checkText")}</Text>
          {preview.warnings.map((w) => (
            <Text key={w} style={styles.warning}>
              • {t(`wineImport.warning.${w}` as TextKey)}
            </Text>
          ))}
        </View>
        <WineForm
          auth={auth}
          initial={initial}
          submitLabel={t("wineForm.save")}
          onSubmit={async (input) => {
            const saved = await wines.create(auth, { ...input, source_url: preview.wine.source_url });
            router.replace(`/wines/${saved.id}`);
          }}
        />
        <BigButton label={t("import.another")} variant="link" onPress={() => setPreview(null)} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Text style={styles.body}>{t("wineImport.intro")}</Text>
      <TextField
        label={t("wineImport.url")}
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

export default function WineImportScreen() {
  return <SignedIn>{(auth) => <Import auth={auth} />}</SignedIn>;
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
