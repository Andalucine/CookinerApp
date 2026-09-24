/**
 * Recetas (portada): the three buttons (Por categorías · Buscar · Nueva receta), the latest
 * recipes and "Mis favoritas". Opened with the notebook parameters it shows someone else's
 * notebook, with the notice "Cuaderno de NOMBRE" (session 8); viewers do not see Nueva receta.
 */
import { router, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { RecipeCard } from "../../components/RecipeCard.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as recipes from "../../services/recipes.ts";
import {
  canAdd,
  notebookParams,
  type OtherNotebook,
  readNotebook,
} from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

const LATEST = 5;

function RecipesHome({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t } = useI18n();
  const carry = notebookParams(notebook); // the notebook travels to the next screens
  const filters = notebook ? { notebook_id: String(notebook.id) } : {};
  const latest = useLoad(
    () => recipes.search(auth, filters, LATEST),
    [auth.token, auth.language, notebook?.id],
  );

  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      <View style={styles.buttons}>
        <BigButton
          label={t("recipes.byCategory")}
          icon="albums-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.push({ pathname: "/recipes/categories", params: carry })}
        />
        <BigButton
          label={t("recipes.search")}
          icon="search"
          iconCircle
          variant="secondary"
          onPress={() => router.push({ pathname: "/recipes/search", params: carry })}
        />
        {canAdd(notebook) ? (
          <BigButton
            label={t("recipes.new")}
            icon="add"
            onPress={() => router.push({ pathname: "/recipes/new", params: carry })}
          />
        ) : null}
      </View>

      <SectionTitle text={t("recipes.latest")} />
      {latest.loading && !latest.data ? (
        <Loading />
      ) : latest.error ? (
        <LoadError error={latest.error} onRetry={latest.reload} />
      ) : latest.data && latest.data.total > 0 ? (
        <View style={styles.list}>
          {latest.data.items.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
          {latest.data.total > LATEST ? (
            <RowButton
              label={t("recipes.seeAll", { count: latest.data.total })}
              strong
              onPress={() =>
                router.push({
                  pathname: "/recipes/list",
                  params: { ...carry, title: notebook ? t("shared.all") : t("recipes.all") },
                })
              }
            />
          ) : null}
          <RowButton
            label={t("recipes.favorites")}
            icon="star-outline"
            onPress={() =>
              router.push({
                pathname: "/recipes/list",
                params: { ...carry, favorites: "true", title: t("recipes.favorites") },
              })
            }
          />
        </View>
      ) : (
        <Text style={styles.empty}>{notebook ? t("shared.empty") : t("recipes.empty")}</Text>
      )}
    </Screen>
  );
}

export default function RecipesHomeScreen() {
  const notebook = readNotebook(useLocalSearchParams());
  return <SignedIn>{(auth) => <RecipesHome auth={auth} notebook={notebook} />}</SignedIn>;
}

const styles = StyleSheet.create({
  buttons: { gap: spacing.m },
  list: { gap: spacing.s },
  empty: { fontSize: fontSize.body, color: colors.muted },
});
