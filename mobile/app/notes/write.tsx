/**
 * Nueva nota and Editar nota (with ?id=), session 9: what it is about (six yellow squares), a
 * title and a big box for the text, as on a notebook page. The title may stay empty: the first line of the text becomes the title.
 * Saving a new note opens it; saving an edit goes back to it. Borrar, with confirmation, only
 * for the notebook owner or whoever wrote the note.
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, StyleSheet, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { NoteKindPicker } from "../../components/NoteKindPicker.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { TITLE_MAX, toNoteInput } from "../../services/noteForm.ts";
import * as notes from "../../services/notes.ts";
import {
  canDeleteItem,
  notebookParams,
  type OtherNotebook,
  readNotebook,
} from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function NoteForm({
  initial,
  submitLabel,
  onSubmit,
}: {
  initial: { title: string; content: string; kind: notes.NoteKind | null };
  submitLabel: string;
  onSubmit: (input: notes.NoteInput) => Promise<void>;
}) {
  const { t } = useI18n();
  const [title, setTitle] = useState(initial.title);
  const [content, setContent] = useState(initial.content);
  const [kind, setKind] = useState(initial.kind);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    const input = toNoteInput(title, content, kind);
    if (!input) {
      setMessage(t("notes.errorEmpty"));
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await onSubmit(input);
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  return (
    <>
      <NoteKindPicker value={kind} onChange={setKind} />
      <TextField
        label={t("notes.title")}
        hint={t("notes.titleHint")}
        value={title}
        onChangeText={setTitle}
        maxLength={TITLE_MAX}
        autoCapitalize="sentences"
      />
      <TextField
        label={t("notes.text")}
        hint={t("notes.textHint")}
        value={content}
        onChangeText={setContent}
        multiline
        autoCapitalize="sentences"
        style={styles.text}
      />
      <Message text={message} />
      <BigButton label={submitLabel} icon="checkmark" loading={busy} onPress={submit} />
    </>
  );
}

function NewNote({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t } = useI18n();
  return (
    <Screen>
      <Stack.Screen options={{ title: t("notes.new") }} />
      <NotebookBanner notebook={notebook} />
      <NoteForm
        initial={{ title: "", content: "", kind: null }}
        submitLabel={t("notes.save")}
        onSubmit={async (input) => {
          const saved = await notes.create(auth, input, notebook?.id);
          router.replace({
            pathname: "/notes/[id]",
            params: { ...notebookParams(notebook), id: String(saved.id) },
          });
        }}
      />
    </Screen>
  );
}

function EditNote({
  auth,
  id,
  notebook,
}: {
  auth: Auth;
  id: number;
  notebook: OtherNotebook | null;
}) {
  const { t } = useI18n();
  const data = useLoad(() => notes.get(auth, id), [auth.token, auth.language, id]);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const note = data.data;

  function confirmDelete() {
    Alert.alert(t("notes.deleteTitle"), t("notes.deleteText", { title: note.title }), [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("notes.delete"), style: "destructive", onPress: remove },
    ]);
  }

  async function remove() {
    setDeleting(true);
    setMessage(null);
    try {
      await notes.remove(auth, note.id);
      router.dismissTo({ pathname: "/notes", params: notebookParams(notebook) });
    } catch (error) {
      setMessage(errorText(error, t));
      setDeleting(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("notes.edit") }} />
      <NotebookBanner notebook={notebook} />
      {/* key: a fresh form when the note is loaded again */}
      <NoteForm
        key={note.updated_at}
        initial={{ title: note.title, content: note.content ?? "", kind: note.kind }}
        submitLabel={t("form.saveChanges")}
        onSubmit={async (input) => {
          await notes.update(auth, note.id, input);
          router.back();
        }}
      />
      {canDeleteItem(notebook, note.author_id, auth.user.id) ? (
        <View style={styles.danger}>
          <Message text={message} />
          <BigButton
            label={t("notes.delete")}
            icon="trash-outline"
            variant="secondary"
            loading={deleting}
            onPress={confirmDelete}
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function WriteNoteScreen() {
  const params = useLocalSearchParams<{ id?: string }>();
  const notebook = readNotebook(params);
  return (
    <SignedIn>
      {(auth) =>
        params.id ? (
          <EditNote auth={auth} id={Number(params.id)} notebook={notebook} />
        ) : (
          <NewNote auth={auth} notebook={notebook} />
        )
      }
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  text: { minHeight: 260, paddingTop: spacing.s, textAlignVertical: "top" },
  danger: { marginTop: spacing.xl, gap: spacing.s },
});
