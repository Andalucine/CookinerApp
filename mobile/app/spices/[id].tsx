/** Ficha de una especia (from a recipe ingredient or from the spice zone): what to use instead,
 * with the proportion and a note; how to make it at home if it is a blend; blends it is part of.
 * Substitutes and blends with a card of their own can be tapped (session 8). */
import { Ionicons } from "@expo/vector-icons";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { cap } from "../../components/SpiceRow.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

export default function SpiceScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t, language } = useI18n();
  const en = language === "en";
  const data = useLoad(() => spices.card(Number(id), language), [id, language]);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const card = data.data;
  const name = cap((en && card.name_en) || card.name);
  const blendNote = card.blend ? (en ? card.blend.note_en : card.blend.note_es) : null;

  return (
    <Screen>
      <Stack.Screen options={{ title: name }} />
      <Text style={styles.title} accessibilityRole="header">
        {name}
      </Text>
      {card.aliases ? (
        <Text style={styles.muted}>{t("spice.aliases", { names: card.aliases })}</Text>
      ) : null}

      <SectionTitle text={t("spice.substitutes")} />
      {card.substitutions.length ? (
        card.substitutions.map((s, index) => {
          const note = en ? s.note_en : s.note_es;
          const label = `${en ? s.substitute_en : s.substitute_es}${s.ratio ? `  (${s.ratio})` : ""}`;
          const target = s.substitute_id;
          const content = (
            <>
              <View style={styles.boxText}>
                <Text style={styles.strong}>{label}</Text>
                {note ? <Text style={styles.body}>{note}</Text> : null}
              </View>
              {target ? <Ionicons name="chevron-forward" size={24} color={colors.ink} /> : null}
            </>
          );
          return target && target !== card.id ? (
            <Pressable
              key={index}
              accessibilityRole="button"
              accessibilityLabel={label}
              onPress={() => router.push(`/spices/${target}`)}
              style={({ pressed }) => [styles.box, styles.boxRow, pressed && styles.pressed]}
            >
              {content}
            </Pressable>
          ) : (
            <View key={index} style={[styles.box, styles.boxRow]}>
              {content}
            </View>
          );
        })
      ) : (
        <Text style={styles.muted}>{t("spice.noSubstitutes")}</Text>
      )}

      {card.blend ? (
        <>
          <SectionTitle text={t("spice.blend")} />
          {card.blend.items.map((item) => (
            <Text key={item.ingredient_id} style={styles.body}>
              • {item.parts} {(en && item.name_en) || item.name}
              {item.is_optional ? ` ${t("spice.optional")}` : ""}
            </Text>
          ))}
          {blendNote ? <Text style={styles.muted}>{blendNote}</Text> : null}
        </>
      ) : null}

      {card.used_in_blends.length ? (
        <>
          <SectionTitle text={t("spice.usedIn")} />
          {card.used_in_blends.map((b) => {
            const blendName = cap((en && b.name_en) || b.name);
            return (
              <Pressable
                key={b.ingredient_id}
                accessibilityRole="button"
                accessibilityLabel={blendName}
                onPress={() => router.push(`/spices/${b.ingredient_id}`)}
                style={({ pressed }) => [styles.box, styles.boxRow, pressed && styles.pressed]}
              >
                <Text style={[styles.strong, styles.boxText]}>{blendName}</Text>
                <Ionicons name="chevron-forward" size={24} color={colors.ink} />
              </Pressable>
            );
          })}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  muted: { fontSize: fontSize.body, color: colors.muted },
  box: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  boxRow: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  boxText: { flex: 1, gap: spacing.xs },
  pressed: { opacity: 0.7 },
  strong: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
});
