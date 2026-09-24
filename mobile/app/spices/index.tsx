/**
 * Especias (portada, session 8): what the marks mean, a search box (results appear below as
 * you type), the button to the equivalence rules, and the seven families one per row with
 * their icon and how many spices each has. No login needed: the catalogue is the same for all.
 */
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import {
  FAMILY_ICONS,
  IconCircle,
  MARK_BLEND,
  MARK_SUBSTITUTES,
} from "../../components/SpiceIcons.tsx";
import { SpiceRow } from "../../components/SpiceRow.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { useSession } from "../../services/session.tsx";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

const MIN_SEARCH = 2;

export default function SpicesHome() {
  const { t, language } = useI18n();
  const { token } = useSession();
  const families = useLoad(() => spices.families({ language, token }), [language, token]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<spices.SpiceSummary[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Search while typing, waiting a moment so that we do not call the API on every letter
  useEffect(() => {
    const text = query.trim();
    if (text.length < MIN_SEARCH) {
      setResults(null);
      setSearchError(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const found = await spices.list({ language, token }, { q: text });
        if (!cancelled) setResults(found);
      } catch (error) {
        if (!cancelled) setSearchError(errorText(error, t));
      }
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, language, token]);

  const searching = query.trim().length >= MIN_SEARCH;
  const familyName = (f: spices.SpiceFamily) => (language === "en" ? f.name_en : f.name_es);

  return (
    <Screen>
      <Text style={styles.intro}>{t("spices.intro")}</Text>
      <View style={styles.legend}>
        <View style={styles.legendRow}>
          <IconCircle name={MARK_SUBSTITUTES} size={36} />
          <Text style={styles.legendText}>{t("spices.legendSubstitutes")}</Text>
        </View>
        <View style={styles.legendRow}>
          <IconCircle name={MARK_BLEND} size={36} />
          <Text style={styles.legendText}>{t("spices.legendBlend")}</Text>
        </View>
      </View>
      <TextField
        label={t("spices.search")}
        hint={t("spices.searchHint")}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
        autoCorrect={false}
        returnKeyType="search"
      />

      {searching ? (
        <View style={styles.list}>
          {searchError ? (
            <Text style={styles.error}>{searchError}</Text>
          ) : results === null ? (
            <Loading />
          ) : results.length === 0 ? (
            <Text style={styles.muted}>{t("spices.noResults")}</Text>
          ) : (
            results.map((spice) => <SpiceRow key={spice.id} spice={spice} />)
          )}
        </View>
      ) : (
        <>
          <RowButton
            label={t("spices.rules")}
            icon="swap-horizontal-outline"
            strong
            onPress={() => router.push("/spices/rules")}
          />

          <SectionTitle text={t("spices.families")} />
          {families.loading && !families.data ? (
            <Loading />
          ) : families.error || !families.data ? (
            <LoadError error={families.error} onRetry={families.reload} />
          ) : (
            <View style={styles.list}>
              {families.data.map((family) => (
                <RowButton
                  key={family.code}
                  label={familyName(family)}
                  icon={FAMILY_ICONS[family.code] ?? "leaf-outline"}
                  count={family.count}
                  onPress={() =>
                    router.push({
                      pathname: "/spices/list",
                      params: { family: family.code, title: familyName(family) },
                    })
                  }
                />
              ))}
            </View>
          )}
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.muted },
  muted: { fontSize: fontSize.body, color: colors.muted },
  error: { fontSize: fontSize.body, color: colors.error },
  list: { gap: spacing.s },
  legend: {
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  legendRow: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  legendText: { flex: 1, fontSize: fontSize.body, color: colors.ink },
});
