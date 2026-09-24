/**
 * Recomendar un vino para una receta (session 8): the wines of my notebook (with a search box),
 * tap one, write why, "Recomendar". Route param: `recipe` (the recipe id) and `title`.
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
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

function Recommend({ auth, recipeId, title }: { auth: Auth; recipeId: number; title: string }) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const list = useLoad(() => wines.search(auth, {}, 200), [auth.token, auth.language]);
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

  const term = query.trim().toLowerCase();
  const items = (list.data?.items ?? []).filter(
    (w) =>
      !term ||
      [w.name, w.winery, w.appellation].some((x) => x && x.toLowerCase().includes(term)),
  );
  return (
    <Screen>
      <Stack.Screen options={{ title: t("recommend.title") }} />
      <Text style={styles.intro}>{t("recommend.pick", { title })}</Text>
      <TextField
        label={t("wines.searchText")}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
      />
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error || !list.data ? (
        <LoadError error={list.error} onRetry={list.reload} />
      ) : list.data.total === 0 ? (
        <>
          <Text style={styles.muted}>{t("recommend.noWines")}</Text>
          <BigButton label={t("wines.new")} icon="add" onPress={() => router.push("/wines/new")} />
        </>
      ) : (
        <View style={styles.list}>
          {items.map((wine) => (
            <WineCard key={wine.id} wine={wine} onPress={() => setChosen(wine)} />
          ))}
          {items.length === 0 ? <Text style={styles.muted}>{t("wines.noResults")}</Text> : null}
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
