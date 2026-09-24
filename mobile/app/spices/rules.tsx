/**
 * Reglas de equivalencia (redesigned in session 8): one card per rule with its icon, the
 * measures as tiles with the sign between them, bars proportional to the volume when every
 * measure is a spoon, the ratio as a badge and the note with its own icon.
 */
import { Ionicons } from "@expo/vector-icons";
import { Fragment } from "react";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Screen } from "../../components/Screen.tsx";
import { IconCircle, ruleIcon } from "../../components/SpiceIcons.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { barWidths, readEquivalence } from "../../services/equivalence.ts";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

/** 3.75 → "3,75 ml" / "3.75 ml"; 15 → "15 ml". */
function formatMl(ml: number, en = false): string {
  const text = String(Math.round(ml * 100) / 100);
  return `${en ? text : text.replace(".", ",")} ml`;
}

function RuleCard({ rule, en }: { rule: spices.EquivalenceRule; en: boolean }) {
  const title = en ? rule.situation_en : rule.situation_es;
  const note = en ? rule.note_en : rule.note_es;
  const { measures, signs, ratio } = readEquivalence(en ? rule.equivalence_en : rule.equivalence_es);
  const bars = barWidths(measures);
  const stacked = measures.length > 2; // "Ajo", "Guindilla", "Medidas"

  return (
    <View style={styles.card} accessibilityLabel={`${title}. ${en ? rule.equivalence_en : rule.equivalence_es}`}>
      <View style={styles.header}>
        <IconCircle name={ruleIcon(rule.situation_es)} />
        <Text style={styles.title}>{title}</Text>
        {ratio ? <Text style={styles.ratio}>{ratio}</Text> : null}
      </View>

      {stacked ? (
        // Three or more measures do not fit side by side: one per row, the sign between rows
        <View style={styles.stack}>
          {measures.map((m, index) => (
            <Fragment key={index}>
              {index > 0 ? <Text style={styles.signStack}>{signs[index - 1]}</Text> : null}
              <View style={styles.tileWide}>
                {m.amount ? <Text style={styles.amount}>{m.amount}</Text> : null}
                <Text style={styles.labelWide}>{m.label}</Text>
              </View>
            </Fragment>
          ))}
        </View>
      ) : (
        <View style={styles.measures}>
          {measures.map((m, index) => (
            <Fragment key={index}>
              {index > 0 ? <Text style={styles.sign}>{signs[index - 1]}</Text> : null}
              <View style={styles.tile}>
                {m.amount ? <Text style={styles.amount}>{m.amount}</Text> : null}
                <Text style={styles.label}>{m.label}</Text>
              </View>
            </Fragment>
          ))}
        </View>
      )}

      {bars ? (
        <View style={styles.bars} accessibilityElementsHidden>
          {bars.map((width, index) => (
            <View key={index} style={styles.barRow}>
              <View style={[styles.bar, { flex: width }, index > 0 && styles.barSecond]} />
              <View style={{ flex: 1 - width }} />
              <Text style={styles.barText}>{formatMl(measures[index].ml ?? 0, en)}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {note ? (
        <View style={styles.noteRow}>
          <Ionicons name="information-circle-outline" size={22} color={colors.muted} />
          <Text style={styles.note}>{note}</Text>
        </View>
      ) : null}
    </View>
  );
}

export default function RulesScreen() {
  const { t, language } = useI18n();
  const data = useLoad(() => spices.rules(language), [language]);

  return (
    <Screen>
      <Text style={styles.intro}>{t("spices.rulesIntro")}</Text>
      {data.loading && !data.data ? (
        <Loading />
      ) : data.error || !data.data ? (
        <LoadError error={data.error} onRetry={data.reload} />
      ) : (
        <View style={styles.list}>
          {data.data.map((rule) => (
            <RuleCard key={rule.id} rule={rule} en={language !== "es"} />
          ))}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.m },
  card: {
    gap: spacing.m,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  title: { flex: 1, fontSize: fontSize.body, fontWeight: "800", color: colors.ink },
  ratio: {
    fontSize: fontSize.small,
    fontWeight: "700",
    color: colors.ink,
    backgroundColor: colors.accentSoft,
    borderRadius: radius.m,
    paddingHorizontal: spacing.s,
    paddingVertical: spacing.xs,
  },
  measures: { flexDirection: "row", alignItems: "stretch", gap: spacing.s },
  stack: { gap: spacing.xs },
  tileWide: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.m,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  labelWide: { flex: 1, fontSize: fontSize.body, color: colors.ink },
  signStack: { fontSize: 24, fontWeight: "700", color: colors.muted, marginLeft: spacing.m },
  tile: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
    padding: spacing.s,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  amount: { fontSize: 30, fontWeight: "800", color: colors.ink, lineHeight: 34, minWidth: 40 },
  label: { fontSize: fontSize.small, color: colors.ink, textAlign: "center" },
  sign: { fontSize: 28, fontWeight: "700", color: colors.muted, alignSelf: "center" },
  bars: { gap: spacing.xs },
  barRow: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  bar: { height: 14, borderRadius: 7, backgroundColor: colors.accent },
  barSecond: { backgroundColor: colors.ink },
  barText: { width: 64, fontSize: fontSize.small, color: colors.muted, textAlign: "right" },
  noteRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.s },
  note: { flex: 1, fontSize: fontSize.small, color: colors.muted, lineHeight: 22 },
});
