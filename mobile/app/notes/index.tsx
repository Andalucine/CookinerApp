/**
 * Notas (portada, session 9): "Nueva nota" in orange, a search box (title and text, results as
 * you type) and every note, last changed first. Opened with the notebook parameters it shows
 * someone else's notebook with the notice "Cuaderno de NOMBRE"; viewers do not see Nueva nota.
 */
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { NoteCard } from "../../components/NoteCard.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as notes from "../../services/notes.ts";
import {
  canAdd,
  notebookParams,
  type OtherNotebook,
  readNotebook,
} from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function NotesHome({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t } = useI18n();
  const carry = notebookParams(notebook);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState(""); // what is searched, a moment after typing
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query.trim()), 300);
    return () => clearTimeout(timer);
  }, [query]);
  const list = useLoad(
    () => notes.list(auth, notebook?.id, search),
    [auth.token, auth.language, notebook?.id, search],
  );

  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      {canAdd(notebook) ? (
        <BigButton
          label={t("notes.new")}
          icon="add"
          onPress={() => router.push({ pathname: "/notes/write", params: carry })}
        />
      ) : null}
      <TextField
        label={t("notes.search")}
        hint={t("notes.searchHint")}
        value={query}
        onChangeText={setQuery}
        returnKeyType="search"
        autoCorrect={false}
        clearButtonMode="while-editing"
      />
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error ? (
        <LoadError error={list.error} onRetry={list.reload} />
      ) : list.data && list.data.length > 0 ? (
        <View style={styles.list}>
          {list.data.map((note) => (
            <NoteCard
              key={note.id}
              note={note}
              onPress={() =>
                router.push({ pathname: "/notes/[id]", params: { ...carry, id: String(note.id) } })
              }
            />
          ))}
        </View>
      ) : (
        <Text style={styles.empty}>
          {search
            ? t("notes.none", { text: search })
            : notebook
              ? t("notes.emptyShared")
              : t("notes.empty")}
        </Text>
      )}
    </Screen>
  );
}

export default function NotesHomeScreen() {
  const notebook = readNotebook(useLocalSearchParams());
  return <SignedIn>{(auth) => <NotesHome auth={auth} notebook={notebook} />}</SignedIn>;
}

const styles = StyleSheet.create({
  list: { gap: spacing.s },
  empty: { fontSize: fontSize.body, color: colors.muted },
});
