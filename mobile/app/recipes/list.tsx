/**
 * Lista de recetas: what a category, a search or "Mis favoritas" found. The filters arrive as
 * route parameters with the API's names; `title` is the heading.
 */
import { Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RecipeCard } from "../../components/RecipeCard.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { cleanFilters, type RecipeFilters } from "../../services/recipeQuery.ts";
import * as recipes from "../../services/recipes.ts";
import { useLoad } from "../../services/useLoad.ts";

const PAGE = 30;

function RecipeList({
  auth,
  filters,
  title,
}: {
  auth: Auth;
  filters: RecipeFilters;
  title: string;
}) {
  const { t } = useI18n();
  const key = JSON.stringify(filters);
  const page = useLoad(() => recipes.search(auth, filters, PAGE), [auth.token, auth.language, key]);
  const [more, setMore] = useState(false);
  const [moreError, setMoreError] = useState<string | null>(null);

  async function loadMore() {
    if (!page.data) return;
    setMore(true);
    setMoreError(null);
    try {
      const next = await recipes.search(auth, filters, PAGE, page.data.items.length);
      page.setData({ total: next.total, items: [...page.data.items, ...next.items] });
    } catch (error) {
      setMoreError(errorText(error, t));
    } finally {
      setMore(false);
    }
  }

  let body;
  if (page.loading && !page.data) body = <Loading />;
  else if (page.error || !page.data) body = <LoadError error={page.error} onRetry={page.reload} />;
  else if (page.data.total === 0) body = <Text style={styles.empty}>{t("recipes.noResults")}</Text>;
  else {
    const { total, items } = page.data;
    body = (
      <View style={styles.list}>
        <Text style={styles.total}>
          {total === 1 ? t("recipes.countOne") : t("recipes.count", { count: total })}
        </Text>
        {items.map((recipe) => (
          <RecipeCard key={recipe.id} recipe={recipe} />
        ))}
        <Message text={moreError} />
        {items.length < total ? (
          <BigButton
            label={t("recipes.loadMore")}
            variant="secondary"
            loading={more}
            onPress={loadMore}
          />
        ) : null}
      </View>
    );
  }

  return (
    <Screen>
      <Stack.Screen options={{ title }} />
      {body}
    </Screen>
  );
}

export default function RecipeListScreen() {
  const params = useLocalSearchParams();
  const { t } = useI18n();
  const filters = cleanFilters(params);
  const title =
    typeof params.title === "string" && params.title ? params.title : t("recipes.results");
  return (
    <SignedIn>{(auth) => <RecipeList auth={auth} filters={filters} title={title} />}</SignedIn>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.s },
  total: { fontSize: fontSize.body, color: colors.muted },
  empty: { fontSize: fontSize.body, color: colors.muted },
});
