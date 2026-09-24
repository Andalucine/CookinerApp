/**
 * Editar sustitutos (session 8): my notebook's list of substitutes for a spice, one per line
 * ("Comino · 1 : 1 · más suave"). It starts from the catalogue's list and replaces it for my
 * notebook; the catalogue is never changed. Route param: `id` (the ingredient).
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { cap } from "../../components/SpiceRow.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as spices from "../../services/spices.ts";
import {
  linesFromSubstitutions,
  parseSubstitutionLines,
} from "../../services/substitutionForm.ts";
import { useLoad } from "../../services/useLoad.ts";
import { catalogName } from "../../services/format.ts";

function Form({ auth, card }: { auth: Auth; card: spices.SpiceCard }) {
  const { t, language } = useI18n();
  const name = cap(catalogName(card, language));
  const [lines, setLines] = useState(() => linesFromSubstitutions(card.substitutions, language));
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    const items = parseSubstitutionLines(lines);
    if (items.length === 0) {
      setError(t("subs.errorNoItems"));
      return;
    }
    if (items.some((i) => i.substitute.toLowerCase() === card.name.toLowerCase())) {
      setError(t("subs.errorSelf"));
      return;
    }
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      await spices.setSubstitutions(auth, card.id, items);
      router.back();
    } catch (e) {
      setMessage(errorText(e, t));
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("subs.title") }} />
      <Text style={styles.intro}>{t("subs.intro", { name })}</Text>
      <TextField
        label={t("subs.lines")}
        hint={t("subs.linesHint")}
        value={lines}
        onChangeText={setLines}
        error={error}
        multiline
        autoCapitalize="sentences"
        autoCorrect={false}
        style={styles.multiline}
      />
      <Message text={message} />
      <View style={styles.buttons}>
        <BigButton label={t("subs.save")} icon="checkmark" loading={busy} onPress={save} />
        <BigButton label={t("common.cancel")} variant="link" onPress={() => router.back()} />
      </View>
    </Screen>
  );
}

function Loader({ auth, id }: { auth: Auth; id: number }) {
  const data = useLoad(() => spices.card(id, auth), [auth.token, auth.language, id]);
  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  return <Form key={`${id}-${data.data.has_own_substitutions}`} auth={auth} card={data.data} />;
}

export default function SubstitutionsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <SignedIn>{(auth) => <Loader auth={auth} id={Number(id)} />}</SignedIn>;
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  multiline: { minHeight: 200, paddingTop: spacing.s, textAlignVertical: "top" },
  buttons: { gap: spacing.s, marginTop: spacing.s },
});
