/**
 * Ficha de un vino (session 8; session 9: the wines are Vinoselección's): name, winery and
 * star; the orange "Comprar en Vinoselección" button with its price (or "agotado"); the type
 * with its serving temperature; the facts in tidy tiles (sweetness, body, ageing, the price
 * band in euros, D.O., country, vintage, grapes); tasting notes; what it goes with (the shop's
 * text, or the pairing rules of its type); "Recomendado para" with the recipes of my notebook
 * that carry it. Nothing is edited here: the shop's page is the source.
 */
import { Ionicons } from "@expo/vector-icons";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { PhotoThumb } from "../../components/Photo.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { ShopPrice } from "../../components/ShopPrice.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { localName } from "../../services/format.ts";
import { useLoad } from "../../services/useLoad.ts";
import { PRICE_BANDS } from "../../services/wineQuery.ts";
import * as wines from "../../services/wines.ts";

function WineScreen({ auth, id }: { auth: Auth; id: number }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [wine, recipes, facets] = await Promise.all([
      wines.get(auth, id),
      wines.recipesOf(auth, id),
      wines.wineFacets(auth.language),
    ]);
    return { wine, recipes, facets };
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
  const { wine, recipes, facets } = data.data;
  // Sweetness, body and ageing are codes ("dry", "reserva"): their names come from the wine
  // catalogue in the person's language, as in the form (session 9: the card showed the codes)
  const facet = (kind: "sweetness" | "body" | "ageing", code: string | null) => {
    if (!code) return null;
    const value = facets[kind].find((v) => v.code === code);
    return value ? localName(value, language) : code;
  };
  const band = PRICE_BANDS.find((b) => b.code === wine.price_range);
  // The price band and the D.O. explain themselves, so they carry no label (Beatriz, s. 8)
  const facts: { key: string; label: string | null; value: string | null }[] = [
    { key: "sweetness", label: t("wineForm.sweetness"), value: facet("sweetness", wine.sweetness) },
    { key: "body", label: t("wineForm.body"), value: facet("body", wine.body) },
    { key: "ageing", label: t("wineForm.ageing"), value: facet("ageing", wine.ageing) },
    { key: "price", label: null, value: band ? t(band.key) : null },
    { key: "appellation", label: null, value: wine.appellation },
    { key: "country", label: t("wineForm.country"), value: wine.country },
    { key: "vintage", label: t("wineForm.vintage"), value: wine.vintage ? String(wine.vintage) : null },
    { key: "grapes", label: t("wineForm.grapes"), value: wine.grapes },
  ];
  const shown = facts.filter((f) => !!f.value);
  const pairing =
    wine.pairing_notes ||
    (wine.pairs_with_categories.length ? wine.pairs_with_categories.join(", ") : null);

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
      <ShopPrice wine={wine} />
      {wine.image_url ? (
        <View style={styles.image}>
          <PhotoThumb url={wine.image_url} size={160} label={t("photo.see")} />
        </View>
      ) : null}

      {wine.category ? (
        <View style={styles.typeBox}>
          <Ionicons name="wine-outline" size={24} color={colors.ink} />
          <Text style={styles.typeText}>{localName(wine.category, language)}</Text>
          {wine.category.serving_temp ? (
            <Text style={styles.temp}>{wine.category.serving_temp}</Text>
          ) : null}
        </View>
      ) : null}

      {shown.length ? (
        <View style={styles.facts}>
          {shown.map((f, index) => (
            <View
              key={f.key}
              style={[
                styles.fact,
                // Grapes take the whole row; the rest go two by two
                f.key === "grapes" || (index === shown.length - 1 && index % 2 === 0)
                  ? styles.factWide
                  : styles.factHalf,
              ]}
            >
              {f.label ? <Text style={styles.factLabel}>{f.label}</Text> : null}
              <Text style={styles.factValue}>{f.value}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {wine.tasting_notes ? (
        <>
          <SectionTitle text={t("wineForm.tasting")} />
          <Text style={styles.body}>{wine.tasting_notes}</Text>
        </>
      ) : null}
      {pairing ? (
        <>
          <SectionTitle text={t("wineForm.pairing")} />
          <Text style={styles.body}>{pairing}</Text>
          {!wine.pairing_notes ? (
            <Text style={styles.muted}>{t("wines.pairingFromRules")}</Text>
          ) : null}
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
  image: { alignItems: "center" },
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
  facts: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  fact: {
    gap: 2,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
  },
  factHalf: { flexBasis: "40%", flexGrow: 1 },
  factWide: { flexBasis: "100%" },
  factLabel: { fontSize: fontSize.small, color: colors.muted },
  factValue: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  muted: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  recipe: { gap: spacing.xs },
  reason: { fontSize: fontSize.small, color: colors.muted, paddingHorizontal: spacing.m },
});
