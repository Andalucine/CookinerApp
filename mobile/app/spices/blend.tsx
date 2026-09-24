/**
 * Nueva mezcla / Editar mezcla (session 8). The ingredients are written one per line, with the
 * parts in front ("2 cúrcuma", "½ canela (opcional)"), like the ingredients of a recipe.
 * Editing a catalogue blend creates the notebook's version; the catalogue is never changed.
 * Route params: `id` (ingredient of the blend to edit) or none for a new one.
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
import { blendErrors, linesFromItems, parseBlendLines } from "../../services/blendForm.ts";
import { errorText } from "../../services/errors.ts";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";
import { catalogName, localText } from "../../services/format.ts";

type Initial = { name: string; note: string; lines: string; nameLocked: boolean };

function BlendForm({
  auth,
  initial,
  editing, // notebook_blend_id when replacing the notebook's own row
  ingredientId,
}: {
  auth: Auth;
  initial: Initial;
  editing: number | null;
  ingredientId: number | null;
}) {
  const { t } = useI18n();
  const [name, setName] = useState(initial.name);
  const [note, setNote] = useState(initial.note);
  const [lines, setLines] = useState(initial.lines);
  const [errors, setErrors] = useState<{ name?: string; items?: string }>({});
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    const input: spices.BlendInput = {
      name: name.trim(),
      note: note.trim() || null,
      items: parseBlendLines(lines),
    };
    const found = blendErrors(input);
    const shown: { name?: string; items?: string } = {};
    if (found.name) shown.name = t("error.required");
    if (found.items === "required") shown.items = t("blend.errorNoItems");
    if (found.items === "self") shown.items = t("blend.errorSelf");
    setErrors(shown);
    if (Object.keys(shown).length) return;
    setBusy(true);
    setMessage(null);
    try {
      const saved = editing
        ? await spices.updateBlend(auth, editing, input)
        : await spices.createBlend(auth, input);
      const target = saved.ingredient_id;
      if (ingredientId) router.back();
      else router.replace(`/spices/${target}`);
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t(ingredientId ? "blend.editTitle" : "blend.newTitle") }} />
      {initial.nameLocked ? (
        <Text style={styles.intro}>{t("blend.versionIntro", { name: initial.name })}</Text>
      ) : (
        <Text style={styles.intro}>{t("blend.newIntro")}</Text>
      )}
      {initial.nameLocked ? null : (
        <TextField
          label={t("blend.name")}
          hint={t("blend.nameHint")}
          value={name}
          onChangeText={setName}
          error={errors.name}
          autoCapitalize="sentences"
        />
      )}
      <TextField
        label={t("blend.items")}
        hint={t("blend.itemsHint")}
        value={lines}
        onChangeText={setLines}
        error={errors.items}
        multiline
        autoCapitalize="none"
        autoCorrect={false}
        style={styles.multiline}
      />
      <TextField
        label={t("blend.note")}
        hint={t("form.optional")}
        value={note}
        onChangeText={setNote}
        multiline
        style={styles.noteField}
      />
      <Message text={message} />
      <View style={styles.buttons}>
        <BigButton label={t("blend.save")} icon="checkmark" loading={busy} onPress={save} />
        <BigButton label={t("common.cancel")} variant="link" onPress={() => router.back()} />
      </View>
    </Screen>
  );
}

function EditBlend({ auth, ingredientId }: { auth: Auth; ingredientId: number }) {
  const { t, language } = useI18n();
  const data = useLoad(() => spices.card(ingredientId, auth), [auth.token, language, ingredientId]);
  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data || !data.data.blend) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const card = data.data;
  const blend = card.blend!;
  // The name of a catalogue blend, or of my version of one, cannot change
  const fromCatalogue = blend.notebook_blend_id === null || card.is_own_version;
  return (
    <BlendForm
      key={`${ingredientId}-${blend.notebook_blend_id ?? "cat"}`}
      auth={auth}
      ingredientId={ingredientId}
      editing={blend.notebook_blend_id}
      initial={{
        name: cap(catalogName(blend, language)),
        note: localText(blend, "note", language) ?? "",
        lines: linesFromItems(blend.items, language, t("blend.optionalWord")),
        nameLocked: fromCatalogue,
      }}
    />
  );
}

export default function BlendScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  return (
    <SignedIn>
      {(auth) =>
        id ? (
          <EditBlend auth={auth} ingredientId={Number(id)} />
        ) : (
          <BlendForm
            auth={auth}
            ingredientId={null}
            editing={null}
            initial={{ name: "", note: "", lines: "", nameLocked: false }}
          />
        )
      }
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  multiline: { minHeight: 160, paddingTop: spacing.s, textAlignVertical: "top" },
  noteField: { minHeight: 80, paddingTop: spacing.s, textAlignVertical: "top" },
  buttons: { gap: spacing.s, marginTop: spacing.s },
});
