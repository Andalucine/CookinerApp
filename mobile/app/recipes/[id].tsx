/**
 * Receta: title, "Receta del cuaderno de NOMBRE" when it is not mine, time, servings, cook,
 * ingredients (the ones with a spice card open it), steps, YouTube video, source with its
 * link, wines with their reason and "(añadido por NOMBRE)". Editar only for owner and editors.
 */
import { Ionicons } from "@expo/vector-icons";
import { router, Stack, useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { YouTubeVideo } from "../../components/YouTubeVideo.tsx";
import { type TextKey, useI18n } from "../../i18n";
import { ApiError } from "../../services/apiClient.ts";
import { errorText } from "../../services/errors.ts";
import {
  formatMinutes,
  ingredientText,
  localName,
  signature,
  siteName,
  splitSteps,
  youtubeId,
} from "../../services/format.ts";
import * as recipes from "../../services/recipes.ts";
import { useLoad } from "../../services/useLoad.ts";

/** Wines follow the owner's plan: a free notebook answers 403 and the part is not shown. */
async function winesOrNothing(auth: Auth, id: number) {
  try {
    return await recipes.wines(auth, id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) return null;
    throw error;
  }
}

function RecipeView({ auth, id }: { auth: Auth; id: number }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [recipe, spices, wines] = await Promise.all([
      recipes.get(auth, id),
      recipes.spices(auth, id),
      winesOrNothing(auth, id),
    ]);
    return { recipe, spiceIds: new Set(spices.map((s) => s.ingredient_id)), wines };
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

  const { recipe, spiceIds, wines } = data.data;
  const video = youtubeId(recipe.youtube_url);
  const steps = splitSteps(recipe.instructions);
  const canEdit = recipe.my_role === "owner" || recipe.my_role === "editor";
  const facts = [
    formatMinutes(recipe.prep_time_minutes),
    recipe.servings ? t("recipe.servings", { count: recipe.servings }) : null,
    recipe.primary_category ? localName(recipe.primary_category, language) : null,
  ].filter(Boolean);
  const when = [...recipe.seasons, ...recipe.occasions].map((x) => localName(x, language));

  async function toggleFavorite() {
    const on = !recipe.is_favorite;
    setFavoriteError(null);
    try {
      await recipes.setFavorite(auth, recipe.id, on);
      data.setData({ ...data.data!, recipe: { ...recipe, is_favorite: on } });
    } catch (error) {
      setFavoriteError(errorText(error, t));
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("recipes.recipe") }} />
      {recipe.notebook_id !== auth.user.notebook_id ? (
        <View style={styles.banner}>
          <Ionicons name="people-outline" size={22} color={colors.ink} />
          <Text style={styles.bannerText}>
            {t("recipe.fromNotebook", { name: recipe.notebook_owner })}
          </Text>
        </View>
      ) : null}

      <View style={styles.titleRow}>
        <Text style={styles.title} accessibilityRole="header">
          {recipe.title}
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={recipe.is_favorite ? t("recipe.favoriteOn") : t("recipe.favoriteOff")}
          onPress={toggleFavorite}
          hitSlop={12}
          style={styles.star}
        >
          <Ionicons
            name={recipe.is_favorite ? "star" : "star-outline"}
            size={34}
            color={recipe.is_favorite ? colors.accent : colors.ink}
          />
        </Pressable>
      </View>
      <Message text={favoriteError} />
      {facts.length ? <Text style={styles.facts}>{facts.join(" · ")}</Text> : null}
      {signature(recipe) ? (
        <Text style={styles.facts}>{t("recipe.cook", { name: signature(recipe)! })}</Text>
      ) : null}
      {recipe.added_by ? (
        <Text style={styles.addedBy}>{t("recipes.addedBy", { name: recipe.added_by })}</Text>
      ) : null}
      {recipe.image_url ? (
        <Image
          source={{ uri: recipe.image_url }}
          style={styles.image}
          accessibilityIgnoresInvertColors
        />
      ) : null}
      {recipe.description ? <Text style={styles.body}>{recipe.description}</Text> : null}

      {recipe.ingredients.length ? (
        <>
          <SectionTitle text={t("recipe.ingredients")} />
          {spiceIds.size ? <Text style={styles.hint}>{t("recipe.spiceHint")}</Text> : null}
          <View style={styles.ingredients}>
            {recipe.ingredients.map((line) => {
              const text = ingredientText(line, language);
              return spiceIds.has(line.ingredient_id) ? (
                <Pressable
                  key={line.position}
                  accessibilityRole="button"
                  accessibilityLabel={text}
                  onPress={() => router.push(`/spices/${line.ingredient_id}`)}
                  style={({ pressed }) => [
                    styles.ingredient,
                    styles.spice,
                    pressed && styles.pressed,
                  ]}
                >
                  <Ionicons name="leaf" size={20} color={colors.ink} />
                  <Text style={styles.ingredientText}>{text}</Text>
                  <Ionicons name="chevron-forward" size={22} color={colors.ink} />
                </Pressable>
              ) : (
                <View key={line.position} style={styles.ingredient}>
                  <Text style={styles.bullet}>•</Text>
                  <Text style={styles.ingredientText}>{text}</Text>
                </View>
              );
            })}
          </View>
        </>
      ) : null}

      {steps.length ? (
        <>
          <SectionTitle text={t("recipe.steps")} />
          {steps.map((step, index) => (
            <View key={index} style={styles.step}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>{index + 1}</Text>
              </View>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}
        </>
      ) : null}

      {video && recipe.youtube_url ? (
        <>
          <SectionTitle text={t("recipe.video")} />
          <YouTubeVideo id={video} url={recipe.youtube_url} />
        </>
      ) : null}

      {when.length ? (
        <>
          <SectionTitle text={t("recipe.when")} />
          <Text style={styles.body}>{when.join(" · ")}</Text>
        </>
      ) : null}

      <SectionTitle text={t("recipe.source")} />
      <Text style={styles.body}>
        {[
          t(`source.${recipe.source_type}` as TextKey),
          recipe.source_name || siteName(recipe.source_url),
        ]
          .filter(Boolean)
          .join(" · ")}
      </Text>
      {recipe.source_url ? (
        <BigButton
          label={t("recipe.openSource")}
          icon="open-outline"
          variant="link"
          onPress={() => WebBrowser.openBrowserAsync(recipe.source_url!)}
        />
      ) : null}

      {wines ? (
        <>
          <SectionTitle text={t("recipe.wines")} />
          {wines.recommended.map((link) => (
            <View key={link.id} style={styles.wine}>
              <Text style={styles.wineName}>
                {[link.wine.name, link.wine.appellation].filter(Boolean).join(" · ")}
              </Text>
              {link.reason ? <Text style={styles.body}>{link.reason}</Text> : null}
              {link.added_by ? (
                <Text style={styles.addedBy}>{t("recipes.addedBy", { name: link.added_by })}</Text>
              ) : null}
            </View>
          ))}
          {wines.suggestion ? (
            <View style={styles.wine}>
              <Text style={styles.hint}>
                {t("recipe.suggestion", { name: localName(wines.suggestion.based_on, language) })}
              </Text>
              {wines.suggestion.wine_types.map((rule) => (
                <View key={localName(rule.wine_category, language)}>
                  <Text style={styles.wineName}>{localName(rule.wine_category, language)}</Text>
                  <Text style={styles.body}>
                    {language === "en" ? rule.reason_en : rule.reason_es}
                  </Text>
                </View>
              ))}
              {wines.suggestion.my_wines.length ? (
                <Text style={styles.body}>
                  {t("recipe.myWinesOfType")}{" "}
                  {wines.suggestion.my_wines.map((w) => w.name).join(", ")}
                </Text>
              ) : null}
            </View>
          ) : null}
          {!wines.recommended.length && !wines.suggestion ? (
            <Text style={styles.hint}>{t("recipe.noWines")}</Text>
          ) : null}
        </>
      ) : null}

      {canEdit ? (
        <View style={styles.actions}>
          <BigButton
            label={t("recipe.edit")}
            icon="create-outline"
            variant="secondary"
            onPress={() =>
              router.push({ pathname: "/recipes/write", params: { id: String(recipe.id) } })
            }
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function RecipeScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <SignedIn>{(auth) => <RecipeView auth={auth} id={Number(id)} />}</SignedIn>;
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  bannerText: { flex: 1, fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  titleRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.s },
  title: { flex: 1, fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  star: { minWidth: 48, minHeight: 48, alignItems: "center", justifyContent: "center" },
  facts: { fontSize: fontSize.body, color: colors.muted },
  addedBy: { fontSize: fontSize.small, color: colors.muted, fontStyle: "italic" },
  image: {
    width: "100%",
    aspectRatio: 4 / 3,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  hint: { fontSize: fontSize.small, color: colors.muted },
  ingredients: { gap: spacing.xs },
  ingredient: { flexDirection: "row", alignItems: "center", gap: spacing.s, minHeight: 40 },
  spice: {
    minHeight: 52,
    paddingHorizontal: spacing.s,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.accent,
    backgroundColor: colors.accentSoft,
  },
  pressed: { opacity: 0.7 },
  bullet: { fontSize: fontSize.large, color: colors.ink, width: 20, textAlign: "center" },
  ingredientText: { flex: 1, fontSize: fontSize.body, color: colors.ink },
  step: { flexDirection: "row", gap: spacing.m, alignItems: "flex-start" },
  stepNumber: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  stepNumberText: { fontSize: fontSize.body, fontWeight: "800", color: colors.ink },
  stepText: { flex: 1, fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  wine: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  wineName: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  actions: { marginTop: spacing.l, gap: spacing.s },
});
