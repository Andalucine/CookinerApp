/** Elegir receta for a meal of the menu (session 9): my recipes, searched by name; tapping
 * one puts it in that meal and goes back to the week. */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RecipeCard } from "../../components/RecipeCard.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as menus from "../../services/menu.ts";
import * as recipes from "../../services/recipes.ts";
import { useLoad } from "../../services/useLoad.ts";

function Pick({
  auth,
  menuId,
  slotId,
  title,
}: {
  auth: Auth;
  menuId: number;
  slotId: number;
  title: string;
}) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setSearch(query.trim()), 300);
    return () => clearTimeout(timer);
  }, [query]);
  const list = useLoad(
    () => recipes.search(auth, search ? { q: search } : {}, 100),
    [auth.token, auth.language, search],
  );
  const [message, setMessage] = useState<string | null>(null);

  async function choose(recipe: recipes.RecipeSummary) {
    setMessage(null);
    try {
      await menus.setSlot(auth, menuId, slotId, { recipe_id: recipe.id, note: null });
      router.back();
    } catch (error) {
      setMessage(errorText(error, t));
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("menu.pickTitle") }} />
      {title ? <Text style={styles.for}>{title}</Text> : null}
      <TextField
        label={t("menu.pickSearch")}
        value={query}
        onChangeText={setQuery}
        autoCorrect={false}
        clearButtonMode="while-editing"
      />
      <Message text={message} />
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error ? (
        <LoadError error={list.error} onRetry={list.reload} />
      ) : list.data && list.data.items.length ? (
        <View style={styles.list}>
          {list.data.items.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} onPress={() => choose(recipe)} />
          ))}
        </View>
      ) : (
        <Text style={styles.muted}>{search ? t("menu.pickNone") : t("recipes.empty")}</Text>
      )}
    </Screen>
  );
}

export default function PickScreen() {
  const params = useLocalSearchParams<{ menu: string; slot: string; title?: string }>();
  return (
    <SignedIn>
      {(auth) => (
        <Pick
          auth={auth}
          menuId={Number(params.menu)}
          slotId={Number(params.slot)}
          title={params.title ?? ""}
        />
      )}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  for: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  list: { gap: spacing.s },
  muted: { fontSize: fontSize.body, color: colors.muted },
});
