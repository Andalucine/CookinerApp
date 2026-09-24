/**
 * Recomendar un vino para una receta (session 8; session 9: from Vinoselección's cellar). With
 * the box empty, my favourites (or, without favourites, wines for sale); writing searches the
 * whole shop by name, winery, grape or D.O. Tap one, write why, "Recomendar".
 * Route params: `recipe` (the recipe id) and `title`.
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { WineCard } from "../../components/WineCard.tsx";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { useLoad } from "../../services/useLoad.ts";
import { wineDetails } from "../../services/wineQuery.ts";
import * as wines from "../../services/wines.ts";

const RESULTS = 40;

function Recommend({ auth, recipeId, title }: { auth: Auth; recipeId: number; title: string }) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [term, setTerm] = useState(""); // what is searched, a moment after typing stops
  useEffect(() => {
    const timer = setTimeout(() => setTerm(query.trim()), 400);
    return () => clearTimeout(timer);
  }, [query]);
  const list = useLoad(async () => {
    if (term.length >= 2) return wines.search(auth, { q: term }, RESULTS);
    const favorites = await wines.search(auth, { favorites: "true" }, RESULTS);
    return favorites.total ? favorites : wines.search(auth, { in_stock: "true" }, RESULTS);
  }, [auth.token, auth.language, term]);
  const [chosen, setChosen] = useState<wines.WineSummary | null>(null);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    if (!chosen) return;
    setBusy(true);
    setMessage(null);
    try {
      await wines.recommend(auth, recipeId, chosen.id, reason.trim() || null);
      router.back();
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  if (chosen) {
    return (
      <Screen>
        <Stack.Screen options={{ title: t("recommend.title") }} />
        <Text style={styles.intro}>{t("recommend.forRecipe", { title })}</Text>
        <View style={styles.chosen}>
          <Text style={styles.chosenName}>{chosen.name}</Text>
          {wineDetails(chosen) ? <Text style={styles.muted}>{wineDetails(chosen)}</Text> : null}
        </View>
        <TextField
          label={t("recommend.reason")}
          hint={t("recommend.reasonHint")}
          value={reason}
          onChangeText={setReason}
          multiline
          style={styles.multiline}
        />
        <Message text={message} />
        <View style={styles.buttons}>
          <BigButton label={t("recommend.submit")} icon="checkmark" loading={busy} onPress={save} />
          <BigButton label={t("recommend.another")} variant="link" onPress={() => setChosen(null)} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("recommend.title") }} />
      <Text style={styles.intro}>{t("recommend.pick", { title })}</Text>
      <TextField
        label={t("wines.searchText")}
        hint={t("wines.searchTextHint")}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
      />
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error || !list.data ? (
        <LoadError error={list.error} onRetry={list.reload} />
      ) : list.data.total === 0 ? (
        <Text style={styles.muted}>{t("wines.noResults")}</Text>
      ) : (
        <View style={styles.list}>
          {list.data.items.map((wine) => (
            <WineCard key={wine.id} wine={wine} onPress={() => setChosen(wine)} />
          ))}
        </View>
      )}
    </Screen>
  );
}

export default function RecommendScreen() {
  const { recipe, title } = useLocalSearchParams<{ recipe: string; title?: string }>();
  return (
    <SignedIn>
      {(auth) => <Recommend auth={auth} recipeId={Number(recipe)} title={title ?? ""} />}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  muted: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  chosen: {
    gap: 2,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  chosenName: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  multiline: { minHeight: 110, paddingTop: spacing.s, textAlignVertical: "top" },
  buttons: { gap: spacing.s },
});
