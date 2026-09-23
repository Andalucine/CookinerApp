/**
 * The recipe form, the same for writing by hand, editing and checking an import before saving.
 * Ingredients and steps are written one per line, like in a paper notebook.
 */
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { type TextKey, useI18n } from "../i18n";
import * as catalog from "../services/catalog.ts";
import type { CategoryNode } from "../services/categoryTree.ts";
import { errorText } from "../services/errors.ts";
import { BUCKET_MINUTES, localName, timeBucket } from "../services/format.ts";
import { ingredientsToLines, linesToIngredients } from "../services/ingredientParser.ts";
import type { RecipeInput, SourceType } from "../services/recipes.ts";
import { useLoad } from "../services/useLoad.ts";
import { BigButton } from "./BigButton.tsx";
import { CategoryPicker } from "./CategoryPicker.tsx";
import { Chips } from "./Chips.tsx";
import { Message } from "./Message.tsx";
import { SectionTitle } from "./SectionTitle.tsx";
import type { Auth } from "./SignedIn.tsx";
import { TextField } from "./TextField.tsx";
import { colors, fontSize, radius, spacing } from "./theme.ts";
import { ToggleChips } from "./ToggleChips.tsx";

const SOURCES: SourceType[] = ["own", "family", "book", "web", "other"];

export function emptyRecipe(language: "es" | "en"): RecipeInput {
  return {
    title: "",
    description: null,
    instructions: null,
    prep_time_minutes: null,
    servings: null,
    cook_name: null,
    source_type: "own",
    source_name: null,
    source_url: null,
    youtube_url: null,
    image_url: null,
    language,
    ingredients: [],
    category_ids: [],
    tag_ids: [],
    season_ids: [],
    occasion_ids: [],
  };
}

const toText = (n: number | null) => (n == null ? "" : String(n));
const orNull = (s: string) => (s.trim() ? s.trim() : null);

export function RecipeForm({
  auth,
  initial,
  submitLabel,
  onSubmit,
  sourceLocked = false,
  notebookId,
}: {
  auth: Auth;
  initial: RecipeInput;
  submitLabel: string;
  onSubmit: (recipe: RecipeInput) => Promise<void>;
  sourceLocked?: boolean; // an import keeps its web source and link
  notebookId?: number;
}) {
  const { t, language } = useI18n();
  const [form, setForm] = useState({
    title: initial.title,
    description: initial.description ?? "",
    ingredients: ingredientsToLines(initial.ingredients, language),
    instructions: initial.instructions ?? "",
    minutes: toText(initial.prep_time_minutes),
    servings: toText(initial.servings),
    cook: initial.cook_name ?? "",
    sourceType: initial.source_type,
    sourceName: initial.source_name ?? "",
    sourceUrl: initial.source_url ?? "",
    youtube: initial.youtube_url ?? "",
  });
  const [categoryIds, setCategoryIds] = useState(initial.category_ids);
  const [seasonIds, setSeasonIds] = useState(initial.season_ids);
  const [occasionIds, setOccasionIds] = useState(initial.occasion_ids);
  const [picking, setPicking] = useState(false);
  const [errors, setErrors] = useState<
    Partial<Record<"title" | "minutes" | "servings" | "sourceUrl", string>>
  >({});
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const lists = useLoad(async () => {
    const [tree, seasons, occasions] = await Promise.all([
      catalog.categories(auth.language),
      catalog.seasons(auth.language),
      catalog.occasions(auth.token, auth.language, notebookId),
    ]);
    return { tree, seasons, occasions };
  }, [auth.token, auth.language, notebookId]);

  const set = (field: keyof typeof form) => (value: string) =>
    setForm((f) => ({ ...f, [field]: value }));
  const toggle = (list: number[], setList: (l: number[]) => void) => (value: number) =>
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  function categoryName(id: number | undefined): string | null {
    if (!id || !lists.data) return null;
    const search = (nodes: CategoryNode[]): CategoryNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node;
        const found = search(node.children);
        if (found) return found;
      }
      return null;
    };
    const node = search(lists.data.tree);
    return node ? localName(node, language) : null;
  }

  function wholeNumber(text: string): number | null | "bad" {
    if (!text.trim()) return null;
    const n = Number(text.trim());
    return Number.isInteger(n) && n >= 0 ? n : "bad";
  }

  async function submit() {
    const minutes = wholeNumber(form.minutes);
    const servings = wholeNumber(form.servings);
    const next: typeof errors = {};
    if (!form.title.trim()) next.title = t("error.required");
    if (minutes === "bad") next.minutes = t("form.errorNumber");
    if (servings === "bad" || servings === 0) next.servings = t("form.errorNumber");
    if (form.sourceType === "web" && !form.sourceUrl.trim())
      next.sourceUrl = t("form.errorWebLink");
    setErrors(next);
    setMessage(null);
    if (Object.keys(next).length) {
      setMessage(t("form.errorsAbove"));
      return;
    }
    const recipe: RecipeInput = {
      ...initial,
      title: form.title.trim(),
      description: orNull(form.description),
      instructions: orNull(form.instructions),
      prep_time_minutes: minutes as number | null,
      servings: servings as number | null,
      cook_name: orNull(form.cook),
      source_type: form.sourceType,
      source_name: orNull(form.sourceName),
      source_url: orNull(form.sourceUrl),
      youtube_url: orNull(form.youtube),
      ingredients: linesToIngredients(form.ingredients, initial.ingredients, language),
      category_ids: categoryIds,
      season_ids: seasonIds,
      occasion_ids: occasionIds,
    };
    setBusy(true);
    try {
      await onSubmit(recipe);
    } catch (error) {
      setMessage(errorText(error, t));
    } finally {
      setBusy(false);
    }
  }

  const primary = categoryName(categoryIds[0]);
  return (
    <View style={styles.form}>
      <TextField
        label={t("form.title")}
        value={form.title}
        onChangeText={set("title")}
        error={errors.title}
      />
      <TextField
        label={t("form.description")}
        hint={t("form.optional")}
        value={form.description}
        onChangeText={set("description")}
        multiline
        style={styles.multiline}
      />

      <SectionTitle text={t("recipe.ingredients")} />
      <TextField
        label={t("form.ingredients")}
        hint={t("form.ingredientsHint")}
        value={form.ingredients}
        onChangeText={set("ingredients")}
        multiline
        autoCapitalize="none"
        style={styles.tall}
      />

      <SectionTitle text={t("recipe.steps")} />
      <TextField
        label={t("form.steps")}
        hint={t("form.stepsHint")}
        value={form.instructions}
        onChangeText={set("instructions")}
        multiline
        style={styles.tall}
      />

      <View style={styles.row}>
        <View style={styles.half}>
          <TextField
            label={t("form.minutes")}
            value={form.minutes}
            onChangeText={set("minutes")}
            keyboardType="number-pad"
            error={errors.minutes}
          />
        </View>
        <View style={styles.half}>
          <TextField
            label={t("form.servings")}
            value={form.servings}
            onChangeText={set("servings")}
            keyboardType="number-pad"
            error={errors.servings}
          />
        </View>
        <Chips
          label={t("search.time")}
          hint={t("form.timeHint")}
          value={timeBucket(Number(form.minutes) || null) ?? ""}
          allowNone
          onChange={(bucket) =>
            setForm((f) => ({
              ...f,
              // Keep the exact minutes when they already fit; otherwise write the button's time
              minutes: !bucket
                ? ""
                : timeBucket(Number(f.minutes) || null) === bucket
                  ? f.minutes
                  : String(BUCKET_MINUTES[bucket as keyof typeof BUCKET_MINUTES]),
            }))
          }
          options={[
            { value: "quick", label: t("time.quick") },
            { value: "medium", label: t("time.medium") },
            { value: "long", label: t("time.long"), wide: true },
          ]}
        />
      </View>
      <TextField
        label={t("search.cook")}
        hint={t("search.cookHint")}
        value={form.cook}
        onChangeText={set("cook")}
      />

      <SectionTitle text={t("form.category")} />
      <View style={styles.category}>
        <Text style={[styles.categoryText, !primary && styles.muted]}>
          {primary ?? t("form.noCategory")}
        </Text>
        <BigButton
          label={primary ? t("form.changeCategory") : t("form.chooseCategory")}
          icon="albums-outline"
          variant="secondary"
          disabled={!lists.data}
          onPress={() => setPicking(true)}
        />
      </View>
      {lists.data ? (
        <>
          <CategoryPicker
            tree={lists.data.tree}
            visible={picking}
            onClose={() => setPicking(false)}
            onPick={(node) => {
              // The chosen one becomes the main category; others the recipe had are kept after it
              setCategoryIds((ids) => [node.id, ...ids.filter((id) => id !== node.id)].slice(0, 3));
              setPicking(false);
            }}
          />
          <ToggleChips
            label={t("search.season")}
            options={lists.data.seasons.map((s) => ({
              value: s.id,
              label: localName(s, language),
            }))}
            selected={seasonIds}
            onToggle={toggle(seasonIds, setSeasonIds)}
            anyLabel={t("search.any")}
            onClear={() => setSeasonIds([])}
          />
          <ToggleChips
            label={t("search.occasion")}
            options={lists.data.occasions.map((o) => ({
              value: o.id,
              label: localName(o, language),
            }))}
            selected={occasionIds}
            onToggle={toggle(occasionIds, setOccasionIds)}
          />
        </>
      ) : null}

      <SectionTitle text={t("recipe.source")} />
      {sourceLocked ? (
        <View style={styles.locked}>
          <Text style={styles.body}>{form.sourceName || form.sourceUrl}</Text>
          <Text style={styles.muted}>{t("form.sourceKept")}</Text>
        </View>
      ) : (
        <>
          <Chips
            label={t("form.sourceType")}
            value={form.sourceType}
            onChange={(value) => setForm((f) => ({ ...f, sourceType: value as SourceType }))}
            options={SOURCES.map((s) => ({ value: s, label: t(`source.${s}` as TextKey) }))}
          />
          {form.sourceType !== "own" ? (
            <TextField
              label={t("form.sourceName")}
              hint={t("form.sourceNameHint")}
              value={form.sourceName}
              onChangeText={set("sourceName")}
            />
          ) : null}
          {form.sourceType === "web" ? (
            <TextField
              label={t("form.sourceUrl")}
              value={form.sourceUrl}
              onChangeText={set("sourceUrl")}
              error={errors.sourceUrl}
              keyboardType="url"
              autoCapitalize="none"
              autoCorrect={false}
            />
          ) : null}
        </>
      )}
      <TextField
        label={t("form.youtube")}
        hint={t("form.youtubeHint")}
        value={form.youtube}
        onChangeText={set("youtube")}
        keyboardType="url"
        autoCapitalize="none"
        autoCorrect={false}
      />

      <Message text={message} />
      <BigButton label={submitLabel} icon="checkmark" loading={busy} onPress={submit} />
    </View>
  );
}

const styles = StyleSheet.create({
  form: { gap: spacing.m },
  multiline: { minHeight: 96, paddingTop: spacing.s, textAlignVertical: "top" },
  tall: { minHeight: 180, paddingTop: spacing.s, textAlignVertical: "top" },
  row: { flexDirection: "row", gap: spacing.m },
  half: { flex: 1 },
  category: { gap: spacing.s },
  categoryText: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  muted: { fontSize: fontSize.body, color: colors.muted },
  body: { fontSize: fontSize.body, color: colors.ink },
  locked: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
});
