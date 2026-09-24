/**
 * Ficha de un vino: name, winery, type with its serving temperature, the facets, D.O., country,
 * grapes, vintage, price; tasting notes; what it goes with; "Recomendado para" with the recipes
 * that carry it; the source; star; Editar for owner and editors (session 8).
 */
import { Ionicons } from "@expo/vector-icons";
import * as WebBrowser from "expo-web-browser";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { localName, siteName } from "../../services/format.ts";
import { useLoad } from "../../services/useLoad.ts";
import * as wines from "../../services/wines.ts";

function WineScreen({ auth, id }: { auth: Auth; id: number }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [wine, recipes] = await Promise.all([wines.get(auth, id), wines.recipesOf(auth, id)]);
    return { wine, recipes };
  }, [auth.token, auth.language, id]);
  const [favoriteError, setFavoriteError] = useState<string | null>(null);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const { wine, recipes } = data.data;
  const facet = (kind: "wine_sweetness" | "wine_body" | "wine_ageing", code: string | null) =>
    code ? t(`${kind}.${code}` as TextKey) : null;
  const facts = [
    facet("wine_sweetness", wine.sweetness),
    facet("wine_body", wine.body),
    facet("wine_ageing", wine.ageing),
    wine.price_range,
  ].filter((x): x is string => !!x);
  const origin = [
    wine.appellation,
    wine.country,
    wine.vintage ? String(wine.vintage) : null,
  ].filter((x): x is string => !!x);
  // The zone shows my own notebook (owner); in another notebook the API refuses if not editor
  const canEdit = true;

  async function toggleFavorite() {
    const on = !wine.is_favorite;
    setFavoriteError(null);
    try {
      await wines.setFavorite(auth, wine.id, on);
      data.setData({ ...data.data!, wine: { ...wine, is_favorite: on } });
    } catch (error) {
      setFavoriteError(errorText(error, t));
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("wines.wine") }} />
      <View style={styles.titleRow}>
        <View style={styles.titleText}>
          <Text style={styles.title} accessibilityRole="header">
            {wine.name}
          </Text>
          {wine.winery ? <Text style={styles.subtitle}>{wine.winery}</Text> : null}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={wine.is_favorite ? t("recipe.favoriteOn") : t("recipe.favoriteOff")}
          onPress={toggleFavorite}
          hitSlop={12}
          style={styles.star}
        >
          <Ionicons
            name={wine.is_favorite ? "star" : "star-outline"}
            size={32}
            color={wine.is_favorite ? colors.accent : colors.ink}
          />
        </Pressable>
      </View>
      <Message text={favoriteError} />

      {wine.category ? (
        <View style={styles.typeBox}>
          <Ionicons name="wine-outline" size={24} color={colors.ink} />
          <Text style={styles.typeText}>
            {[wine.category.parent, wine.category]
              .filter((x): x is wines.WineCategoryRef => !!x)
              .map((x) => localName(x, language))
              .join(" ▸ ")}
          </Text>
          {wine.category.serving_temp ? (
            <Text style={styles.temp}>{wine.category.serving_temp}</Text>
          ) : null}
        </View>
      ) : null}

      {facts.length ? (
        <View style={styles.chips}>
          {facts.map((f) => (
            <View key={f} style={styles.chip}>
              <Text style={styles.chipText}>{f}</Text>
            </View>
          ))}
        </View>
      ) : null}
      {origin.length ? <Text style={styles.body}>{origin.join(" · ")}</Text> : null}
      {wine.grapes ? <Text style={styles.muted}>{t("wines.grapes", { grapes: wine.grapes })}</Text> : null}
      {wine.added_by ? (
        <Text style={styles.muted}>{t("recipes.addedBy", { name: wine.added_by })}</Text>
      ) : null}

      {wine.tasting_notes ? (
        <>
          <SectionTitle text={t("wineForm.tasting")} />
          <Text style={styles.body}>{wine.tasting_notes}</Text>
        </>
      ) : null}
      {wine.pairing_notes ? (
        <>
          <SectionTitle text={t("wineForm.pairing")} />
          <Text style={styles.body}>{wine.pairing_notes}</Text>
        </>
      ) : null}

      <SectionTitle text={t("wines.recommendedFor")} />
      {recipes.length ? (
        <View style={styles.list}>
          {recipes.map((r) => (
            <View key={r.link_id} style={styles.recipe}>
              <RowButton
                label={r.title}
                icon="book-outline"
                onPress={() => router.push(`/recipes/${r.recipe_id}`)}
              />
              {r.reason ? <Text style={styles.reason}>{r.reason}</Text> : null}
            </View>
          ))}
        </View>
      ) : (
        <Text style={styles.muted}>{t("wines.recommendedForNone")}</Text>
      )}

      {wine.source_url ? (
        <>
          <SectionTitle text={t("recipe.source")} />
          <Text style={styles.body}>{siteName(wine.source_url) ?? wine.source_url}</Text>
          <BigButton
            label={t("wines.openSource")}
            icon="open-outline"
            variant="link"
            onPress={() => WebBrowser.openBrowserAsync(wine.source_url!)}
          />
        </>
      ) : null}

      {canEdit ? (
        <View style={styles.actions}>
          <BigButton
            label={t("recipe.edit")}
            icon="create-outline"
            variant="secondary"
            onPress={() => router.push({ pathname: "/wines/write", params: { id: String(wine.id) } })}
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function WineDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <SignedIn>{(auth) => <WineScreen auth={auth} id={Number(id)} />}</SignedIn>;
}

const styles = StyleSheet.create({
  titleRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.s },
  titleText: { flex: 1, gap: 2 },
  title: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  subtitle: { fontSize: fontSize.body, color: colors.muted },
  star: { padding: spacing.xs },
  typeBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  typeText: { flex: 1, fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  temp: { fontSize: fontSize.small, fontWeight: "600", color: colors.ink },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  chip: {
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.xs,
    borderRadius: radius.l,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
  },
  chipText: { fontSize: fontSize.small, fontWeight: "600", color: colors.ink },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  muted: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  recipe: { gap: spacing.xs },
  reason: { fontSize: fontSize.small, color: colors.muted, paddingHorizontal: spacing.m },
  actions: { marginTop: spacing.l, gap: spacing.s },
});
