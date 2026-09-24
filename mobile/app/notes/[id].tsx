/**
 * A note (session 9): the yellow square and the name of its kind, the title, the day it was
 * changed and by whom, the text as it was written (line breaks kept, it can be selected and
 * copied) and Editar for the owner and editors.
 */
import { router, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { NoteKindIcon } from "../../components/NoteKindIcon.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { kindLabel } from "../../services/noteKinds.ts";
import * as notes from "../../services/notes.ts";
import {
  canAdd,
  notebookParams,
  type OtherNotebook,
  readNotebook,
  shortDate,
} from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function NoteScreen({
  auth,
  id,
  notebook,
}: {
  auth: Auth;
  id: number;
  notebook: OtherNotebook | null;
}) {
  const { t, language } = useI18n();
  const data = useLoad(() => notes.get(auth, id), [auth.token, auth.language, id]);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const note = data.data;
  const kind = kindLabel(note.kind);
  const people = [
    note.added_by ? t("recipes.addedBy", { name: note.added_by }) : null,
    note.edited_by && note.edited_by !== note.added_by
      ? t("notes.editedBy", { name: note.edited_by })
      : null,
  ].filter(Boolean);

  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      <View style={styles.head}>
        <View style={styles.kind}>
          <NoteKindIcon kind={note.kind} size={44} />
          {kind ? <Text style={styles.kindName}>{t(kind)}</Text> : null}
        </View>
        <Text style={styles.title} accessibilityRole="header">
          {note.title}
        </Text>
        <Text style={styles.muted}>
          {t("notes.changed", { date: shortDate(note.updated_at, language) })}
        </Text>
        {people.length ? <Text style={styles.muted}>{people.join(" ")}</Text> : null}
      </View>
      {note.content ? (
        <Text style={styles.body} selectable>
          {note.content}
        </Text>
      ) : null}
      {canAdd(notebook) ? (
        <View style={styles.actions}>
          <BigButton
            label={t("recipe.edit")}
            icon="create-outline"
            variant="secondary"
            onPress={() =>
              router.push({
                pathname: "/notes/write",
                params: { ...notebookParams(notebook), id: String(note.id) },
              })
            }
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function NoteDetailScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const notebook = readNotebook(params);
  return (
    <SignedIn>
      {(auth) => <NoteScreen auth={auth} id={Number(params.id)} notebook={notebook} />}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  head: { gap: spacing.xs },
  kind: { flexDirection: "row", alignItems: "center", gap: spacing.s, marginBottom: spacing.xs },
  kindName: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  title: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  muted: { fontSize: fontSize.small, color: colors.muted },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  actions: { marginTop: spacing.l },
});
