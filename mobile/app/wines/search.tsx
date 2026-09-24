/** Buscar vinos: name, winery, grape or D.O.; type, sweetness, body, ageing and price with the
 * tidy buttons. "Buscar vinos" opens the list with those filters. */
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { localName } from "../../services/format.ts";
import { useLoad } from "../../services/useLoad.ts";
import type { WineFilters } from "../../services/wineQuery.ts";
import * as wines from "../../services/wines.ts";

const EMPTY = { q: "", category_id: "", sweetness: "", body: "", ageing: "", price_range: "" };

function Search({ auth }: { auth: Auth }) {
  const { t, language } = useI18n();
  const [form, setForm] = useState(EMPTY);
  const set = (field: keyof typeof EMPTY) => (value: string) =>
    setForm((f) => ({ ...f, [field]: value }));
  const catalog = useLoad(async () => {
    const [types, facets] = await Promise.all([
      wines.wineCategories(auth.language),
      wines.wineFacets(auth.language),
    ]);
    return { types, facets };
  }, [auth.language]);

  function submit() {
    const filters: WineFilters = {};
    if (form.q.trim()) filters.q = form.q.trim();
    for (const key of ["category_id", "sweetness", "body", "ageing", "price_range"] as const) {
      if (form[key]) filters[key] = form[key];
    }
    router.push({ pathname: "/wines/list", params: { ...filters, title: t("recipes.results") } });
  }

  const any = { value: "", label: t("search.any"), wide: true };
  const facet = (values: wines.FacetValue[]) => [
    any,
    ...values.map((v) => ({ value: v.code, label: localName(v, language) })),
  ];
  return (
    <Screen>
      <TextField
        label={t("wines.searchText")}
        hint={t("wines.searchTextHint")}
        value={form.q}
        onChangeText={set("q")}
        autoCapitalize="none"
        returnKeyType="search"
        onSubmitEditing={submit}
      />
      {catalog.data ? (
        <>
          <Chips
            label={t("wineForm.type")}
            value={form.category_id}
            onChange={set("category_id")}
            options={[
              any,
              ...catalog.data.types.map((n) => ({ value: String(n.id), label: localName(n, language) })),
            ]}
          />
          <Chips
            label={t("wineForm.sweetness")}
            value={form.sweetness}
            onChange={set("sweetness")}
            options={facet(catalog.data.facets.sweetness)}
          />
          <Chips
            label={t("wineForm.body")}
            value={form.body}
            onChange={set("body")}
            options={facet(catalog.data.facets.body)}
          />
          <Chips
            label={t("wineForm.ageing")}
            value={form.ageing}
            onChange={set("ageing")}
            options={facet(catalog.data.facets.ageing)}
          />
          <Chips
            label={t("wineForm.price")}
            value={form.price_range}
            onChange={set("price_range")}
            options={[any, ...catalog.data.facets.price_ranges.map((p) => ({ value: p, label: p }))]}
          />
        </>
      ) : null}
      <View style={styles.buttons}>
        <BigButton label={t("wines.searchSubmit")} icon="search" onPress={submit} />
        <BigButton label={t("search.clear")} variant="link" onPress={() => setForm(EMPTY)} />
      </View>
    </Screen>
  );
}

export default function WineSearchScreen() {
  return <SignedIn>{(auth) => <Search auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({ buttons: { gap: spacing.s, marginTop: spacing.s } });
