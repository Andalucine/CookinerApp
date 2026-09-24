/** One recipe in a list: title, time, cook and category; star when it is a favourite. */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { formatMinutes, localName, signature } from "../services/format.ts";
import type { RecipeSummary } from "../services/recipes.ts";
import { colors, fontSize, radius, spacing } from "./theme.ts";

export function RecipeCard({
  recipe,
  onPress,
}: {
  recipe: RecipeSummary;
  onPress?: () => void; // instead of opening the recipe (the menu picker, session 9)
}) {
  const { t, language } = useI18n();
  const details = [
    formatMinutes(recipe.prep_time_minutes),
    signature(recipe),
    recipe.primary_category ? localName(recipe.primary_category, language) : null,
  ].filter(Boolean);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={[recipe.title, ...details].join(", ")}
      onPress={onPress ?? (() => router.push(`/recipes/${recipe.id}`))}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.text}>
        <Text style={styles.title}>{recipe.title}</Text>
        {details.length ? <Text style={styles.details}>{details.join(" · ")}</Text> : null}
        {recipe.added_by ? (
          <Text style={styles.details}>{t("recipes.addedBy", { name: recipe.added_by })}</Text>
        ) : null}
      </View>
      {recipe.is_favorite ? <Ionicons name="star" size={24} color={colors.accent} /> : null}
      <Ionicons name="chevron-forward" size={24} color={colors.ink} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    minHeight: 72,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  pressed: { opacity: 0.7 },
  text: { flex: 1, gap: 2 },
  title: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  details: { fontSize: fontSize.small, color: colors.muted },
});
