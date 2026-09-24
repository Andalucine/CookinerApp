/**
 * Especias (portada, session 8): a search box (results appear below as you type), the button to
 * the equivalence rules, and the seven families in the two-column grid with how many spices
 * each has. No login needed: the catalogue is the same for everyone.
 */
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { wideFlags } from "../../components/gridLayout.ts";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { SpiceRow } from "../../components/SpiceRow.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

const MIN_SEARCH = 2;

export default function SpicesHome() {
  const { t, language } = useI18n();
  const families = useLoad(() => spices.families(language), [language]);
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
        const found = await spices.list(language, { q: text });
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
  }, [query, language]);

  const searching = query.trim().length >= MIN_SEARCH;
  const familyName = (f: spices.SpiceFamily) => (language === "en" ? f.name_en : f.name_es);

  return (
    <Screen>
      <Text style={styles.intro}>{t("spices.intro")}</Text>
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
            <View style={styles.grid}>
              {families.data.map((family, index, all) => {
                const wide = wideFlags(all.map(() => ({})))[index];
                return (
                  <Pressable
                    key={family.code}
                    accessibilityRole="button"
                    accessibilityLabel={`${familyName(family)}, ${family.count}`}
                    onPress={() =>
                      router.push({
                        pathname: "/spices/list",
                        params: { family: family.code, title: familyName(family) },
                      })
                    }
                    style={({ pressed }) => [
                      styles.tile,
                      wide ? styles.wide : styles.half,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={styles.tileName}>{familyName(family)}</Text>
                    <Text style={styles.tileCount}>{family.count}</Text>
                  </Pressable>
                );
              })}
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
  // Two equal columns; the odd one out takes the whole row (rule of the app, session 7)
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  tile: {
    minHeight: 96,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
    justifyContent: "space-between",
  },
  half: { flexBasis: "40%", flexGrow: 1 },
  wide: { flexBasis: "100%" },
  pressed: { opacity: 0.7 },
  tileName: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  tileCount: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink, textAlign: "right" },
});
