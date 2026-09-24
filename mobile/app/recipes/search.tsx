/**
 * Buscar recetas: by one or more ingredients, words of the title, time, cook, source, season
 * and occasion. "Buscar recetas" opens the list with those filters. Also for someone else's
 * notebook (its own occasions included).
 */
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as catalog from "../../services/catalog.ts";
import { localName } from "../../services/format.ts";
import { type RecipeFilters, splitIngredients } from "../../services/recipeQuery.ts";
import { notebookParams, type OtherNotebook, readNotebook } from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

const EMPTY = { ingredients: "", q: "", time: "", cook: "", source: "", season: "", occasion: "" };

function Search({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t, language } = useI18n();
  const [form, setForm] = useState(EMPTY);
  const set = (field: keyof typeof EMPTY) => (value: string) =>
    setForm((f) => ({ ...f, [field]: value }));
  const lists = useLoad(async () => {
    const [seasons, occasions] = await Promise.all([
      catalog.seasons(auth.language),
      catalog.occasions(auth.token, auth.language, notebook?.id),
    ]);
    return { seasons, occasions };
  }, [auth.token, auth.language, notebook?.id]);

  function submit() {
    const filters: RecipeFilters = {
      ingredients: splitIngredients(form.ingredients).join(",") || undefined,
      q: form.q.trim() || undefined,
      time: form.time || undefined,
      cook: form.cook.trim() || undefined,
      source: form.source.trim() || undefined,
      season_id: form.season || undefined,
      occasion_id: form.occasion || undefined,
    };
    const params: Record<string, string> = {
      ...notebookParams(notebook), // includes notebook_id, the filter the API needs
      title: t("recipes.results"),
    };
    for (const [key, value] of Object.entries(filters)) if (value) params[key] = value;
    router.push({ pathname: "/recipes/list", params });
  }

  const any = { value: "", label: t("search.any"), wide: true };
  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      <TextField
        label={t("search.ingredients")}
        hint={t("search.ingredientsHint")}
        value={form.ingredients}
        onChangeText={set("ingredients")}
        autoCapitalize="none"
        returnKeyType="search"
        onSubmitEditing={submit}
      />
      <TextField label={t("search.words")} value={form.q} onChangeText={set("q")} />
      <Chips
        label={t("search.time")}
        value={form.time}
        onChange={set("time")}
        options={[
          { value: "", label: t("search.any") },
          { value: "quick", label: t("time.quick") },
          { value: "medium", label: t("time.medium") },
          { value: "long", label: t("time.long") },
        ]}
      />
      <TextField
        label={t("search.cook")}
        hint={t("search.cookHint")}
        value={form.cook}
        onChangeText={set("cook")}
      />
      <TextField
        label={t("search.source")}
        hint={t("search.sourceHint")}
        value={form.source}
        onChangeText={set("source")}
        autoCapitalize="none"
      />
      {lists.data ? (
        <>
          <Chips
            label={t("search.season")}
            value={form.season}
            onChange={set("season")}
            options={[
              any,
              ...lists.data.seasons.map((s) => ({
                value: String(s.id),
                label: localName(s, language),
              })),
            ]}
          />
          <Chips
            label={t("search.occasion")}
            value={form.occasion}
            onChange={set("occasion")}
            allowNone
            hint={t("search.occasionHint")}
            options={[
              ...lists.data.occasions.map((o) => ({
                value: String(o.id),
                label: localName(o, language),
              })),
            ]}
          />
        </>
      ) : null}
      <View style={styles.buttons}>
        <BigButton label={t("search.submit")} icon="search" onPress={submit} />
        <BigButton label={t("search.clear")} variant="link" onPress={() => setForm(EMPTY)} />
      </View>
    </Screen>
  );
}

export default function SearchScreen() {
  const notebook = readNotebook(useLocalSearchParams());
  return <SignedIn>{(auth) => <Search auth={auth} notebook={notebook} />}</SignedIn>;
}

const styles = StyleSheet.create({ buttons: { gap: spacing.s, marginTop: spacing.s } });
