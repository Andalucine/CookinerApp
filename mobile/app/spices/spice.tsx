/**
 * Nueva especia / Editar especia (session 8): a spice of my notebook, in one of the seven
 * families, with its other names. Route params: `family` (preselected for a new one) or
 * `id` (the notebook spice row to edit) with `ingredient` (its ingredient id).
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
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
import { useLoad } from "../../services/useLoad.ts";
import { catalogName, localName } from "../../services/format.ts";

type Initial = { name: string; family: string; aliases: string };

function Form({
  auth,
  initial,
  editing,
  families,
}: {
  auth: Auth;
  initial: Initial;
  editing: number | null; // notebook spice id
  families: spices.SpiceFamily[];
}) {
  const { t, language } = useI18n();
  const [name, setName] = useState(initial.name);
  const [family, setFamily] = useState(initial.family);
  const [aliases, setAliases] = useState(initial.aliases);
  const [nameError, setNameError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    if (!name.trim()) {
      setNameError(t("error.required"));
      return;
    }
    setNameError(null);
    setMessage(null);
    setBusy(true);
    const body = { name: name.trim(), family, aliases: aliases.trim() || null };
    try {
      const saved = editing
        ? await spices.updateSpice(auth, editing, body)
        : await spices.createSpice(auth, body);
      if (editing) router.back();
      else router.replace(`/spices/${saved.ingredient_id}`);
    } catch (e) {
      setMessage(errorText(e, t));
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t(editing ? "ownSpice.editTitle" : "ownSpice.newTitle") }} />
      <Text style={styles.intro}>{t("ownSpice.intro")}</Text>
      <TextField
        label={t("ownSpice.name")}
        value={name}
        onChangeText={setName}
        error={nameError}
        autoCapitalize="sentences"
      />
      <Chips
        label={t("ownSpice.family")}
        value={family}
        onChange={setFamily}
        options={families.map((f) => ({
          value: f.code,
          label: localName(f, language),
        }))}
      />
      <TextField
        label={t("ownSpice.aliases")}
        hint={t("ownSpice.aliasesHint")}
        value={aliases}
        onChangeText={setAliases}
        autoCapitalize="none"
      />
      <Message text={message} />
      <View style={styles.buttons}>
        <BigButton label={t("ownSpice.save")} icon="checkmark" loading={busy} onPress={save} />
        <BigButton label={t("common.cancel")} variant="link" onPress={() => router.back()} />
      </View>
    </Screen>
  );
}

function Loader({
  auth,
  family,
  editing,
  ingredient,
}: {
  auth: Auth;
  family: string;
  editing: number | null;
  ingredient: number | null;
}) {
  const { language } = useI18n();
  const data = useLoad(async () => {
    const [families, card] = await Promise.all([
      spices.families(auth),
      ingredient ? spices.card(ingredient, auth) : Promise.resolve(null),
    ]);
    return { families, card };
  }, [auth.token, language, ingredient]);
  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const card = data.data.card;
  return (
    <Form
      key={card ? `${card.id}-${card.aliases}` : "new"}
      auth={auth}
      editing={editing}
      families={data.data.families}
      initial={{
        name: card ? cap(catalogName(card, language)) : "",
        family: card?.family ?? family,
        aliases: card?.aliases ?? "",
      }}
    />
  );
}

export default function OwnSpiceScreen() {
  const params = useLocalSearchParams<{ family?: string; id?: string; ingredient?: string }>();
  return (
    <SignedIn>
      {(auth) => (
        <Loader
          auth={auth}
          family={params.family || "herbs"}
          editing={params.id ? Number(params.id) : null}
          ingredient={params.ingredient ? Number(params.ingredient) : null}
        />
      )}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  buttons: { gap: spacing.s, marginTop: spacing.s },
});
