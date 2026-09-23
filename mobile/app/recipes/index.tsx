/**
 * Recetas (portada): the three buttons (Por categorías · Buscar · Nueva receta), the latest
 * recipes of my notebook and "Mis favoritas".
 */
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { RecipeCard } from "../../components/RecipeCard.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as recipes from "../../services/recipes.ts";
import { useLoad } from "../../services/useLoad.ts";

const LATEST = 5;

function RecipesHome({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const latest = useLoad(() => recipes.search(auth, {}, LATEST), [auth.token, auth.language]);

  return (
    <Screen>
      <View style={styles.buttons}>
        <BigButton
          label={t("recipes.byCategory")}
          icon="albums-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.push("/recipes/categories")}
        />
        <BigButton
          label={t("recipes.search")}
          icon="search"
          iconCircle
          variant="secondary"
          onPress={() => router.push("/recipes/search")}
        />
        <BigButton
          label={t("recipes.new")}
          icon="add"
          onPress={() => router.push("/recipes/new")}
        />
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
                router.push({ pathname: "/recipes/list", params: { title: t("recipes.all") } })
              }
            />
          ) : null}
          <RowButton
            label={t("recipes.favorites")}
            icon="star-outline"
            onPress={() =>
              router.push({
                pathname: "/recipes/list",
                params: { favorites: "true", title: t("recipes.favorites") },
              })
            }
          />
        </View>
      ) : (
        <Text style={styles.empty}>{t("recipes.empty")}</Text>
      )}
    </Screen>
  );
}

export default function RecipesHomeScreen() {
  return <SignedIn>{(auth) => <RecipesHome auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  buttons: { gap: spacing.m },
  list: { gap: spacing.s },
  empty: { fontSize: fontSize.body, color: colors.muted },
});
