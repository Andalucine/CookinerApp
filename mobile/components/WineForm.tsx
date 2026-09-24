/**
 * The wine form (new and edit): name, winery, type (chosen level by level like the recipe
 * category), sweetness, body and ageing with the tidy buttons, the price bands, D.O., grapes,
 * country and vintage side by side, tasting notes, what it goes with (prefilled from the
 * pairing rules when imported), and the source when it came from a web.
 */
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { errorText } from "../services/errors.ts";
import { localName } from "../services/format.ts";
import { useLoad } from "../services/useLoad.ts";
import { parseVintage } from "../services/wineQuery.ts";
import * as wines from "../services/wines.ts";
import { BigButton } from "./BigButton.tsx";
import { CategoryPicker } from "./CategoryPicker.tsx";
import type { CategoryNode } from "../services/categoryTree.ts";
import { Chips } from "./Chips.tsx";
import { LoadError, Loading } from "./LoadState.tsx";
import { Message } from "./Message.tsx";
import { PriceChoice } from "./PriceChoice.tsx";
import { SectionTitle } from "./SectionTitle.tsx";
import { ShopPrice } from "./ShopPrice.tsx";
import type { Auth } from "./SignedIn.tsx";
import { TextField } from "./TextField.tsx";
import { colors, fontSize, spacing } from "./theme.ts";

export function emptyWine(): wines.WineInput {
  return {
    name: "",
    winery: null,
    category_id: null,
    sweetness: null,
    body: null,
    ageing: null,
    country: null,
    appellation: null,
    grapes: null,
    vintage: null,
    price_range: null,
    tasting_notes: null,
    pairing_notes: null,
    source_url: null,
    source_name: null,
    source_price: null,
    image_url: null,
  };
}

type Texts = {
  name: string;
  winery: string;
  country: string;
  appellation: string;
  grapes: string;
  vintage: string;
  tasting: string;
  pairing: string;
  source: string;
};

function fromInput(input: wines.WineInput): Texts {
  return {
    name: input.name,
    winery: input.winery ?? "",
    country: input.country ?? "",
    appellation: input.appellation ?? "",
    grapes: input.grapes ?? "",
    vintage: input.vintage ? String(input.vintage) : "",
    tasting: input.tasting_notes ?? "",
    pairing: input.pairing_notes ?? "",
    source: input.source_url ?? "",
  };
}

const orNull = (s: string) => (s.trim() ? s.trim() : null);

/** Wine types as the category picker expects them (level and examples added). */
function asTree(nodes: wines.WineCategoryNode[], level = 1): CategoryNode[] {
  return nodes.map((n) => ({
    id: n.id,
    slug: n.slug,
    level,
    examples_es: n.examples_es,
    name_es: n.name_es,
    name_en: n.name_en,
    children: asTree(n.children, level + 1),
  }));
}

function findType(
  nodes: wines.WineCategoryNode[],
  id: number | null,
): { node: wines.WineCategoryNode; parent: wines.WineCategoryNode | null } | null {
  if (id === null) return null;
  for (const root of nodes) {
    if (root.id === id) return { node: root, parent: null };
    const child = root.children.find((c) => c.id === id);
    if (child) return { node: child, parent: root };
  }
  return null;
}

export function WineForm({
  auth,
  initial,
  submitLabel,
  onSubmit,
}: {
  auth: Auth;
  initial: wines.WineInput;
  submitLabel: string;
  onSubmit: (input: wines.WineInput) => Promise<void>;
}) {
  const { t, language } = useI18n();
  const catalog = useLoad(async () => {
    const [types, facets] = await Promise.all([
      wines.wineCategories(auth.language),
      wines.wineFacets(auth.language),
    ]);
    return { types, facets };
  }, [auth.language]);
  const [texts, setTexts] = useState<Texts>(() => fromInput(initial));
  const [categoryId, setCategoryId] = useState<number | null>(initial.category_id);
  const [facets, setFacets] = useState({
    sweetness: initial.sweetness ?? "",
    body: initial.body ?? "",
    ageing: initial.ageing ?? "",
    price_range: initial.price_range ?? "",
  });
  const [picking, setPicking] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; vintage?: string }>({});
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const setText = (field: keyof Texts) => (value: string) =>
    setTexts((v) => ({ ...v, [field]: value }));
  const setFacet = (field: keyof typeof facets) => (value: string) =>
    setFacets((v) => ({ ...v, [field]: value }));

  if (catalog.loading && !catalog.data) return <Loading />;
  if (catalog.error || !catalog.data) {
    return <LoadError error={catalog.error} onRetry={catalog.reload} />;
  }
  const { types, facets: options } = catalog.data;
  const chosen = findType(types, categoryId);
  const any = { value: "", label: t("search.any"), wide: true };
  const facetOptions = (values: wines.FacetValue[]) => [
    any,
    ...values.map((v) => ({ value: v.code, label: localName(v, language) })),
  ];

  async function submit() {
    const vintage = parseVintage(texts.vintage);
    const found: { name?: string; vintage?: string } = {};
    if (!texts.name.trim()) found.name = t("error.required");
    if (Number.isNaN(vintage)) found.vintage = t("wineForm.errorVintage");
    setErrors(found);
    if (Object.keys(found).length) {
      setMessage(t("form.errorsAbove"));
      return;
    }
    setMessage(null);
    setBusy(true);
    try {
      await onSubmit({
        name: texts.name.trim(),
        winery: orNull(texts.winery),
        category_id: categoryId,
        sweetness: facets.sweetness || null,
        body: facets.body || null,
        ageing: facets.ageing || null,
        country: orNull(texts.country),
        appellation: orNull(texts.appellation),
        grapes: orNull(texts.grapes),
        vintage: Number.isNaN(vintage) ? null : vintage,
        price_range: facets.price_range || null,
        tasting_notes: orNull(texts.tasting),
        pairing_notes: orNull(texts.pairing),
        source_url: orNull(texts.source),
        // What the shop said when it was imported travels untouched with the wine
        source_name: orNull(texts.source) ? initial.source_name : null,
        source_price: orNull(texts.source) ? initial.source_price : null,
        image_url: initial.image_url,
      });
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  return (
    <View style={styles.form}>
      <TextField
        label={t("wineForm.name")}
        value={texts.name}
        onChangeText={setText("name")}
        error={errors.name}
        autoCapitalize="words"
      />
      <TextField
        label={t("wineForm.winery")}
        hint={t("form.optional")}
        value={texts.winery}
        onChangeText={setText("winery")}
        autoCapitalize="words"
      />

      <SectionTitle text={t("wineForm.type")} />
      {chosen ? (
        <Text style={styles.chosen}>
          {[chosen.parent, chosen.node]
            .filter((x): x is wines.WineCategoryNode => !!x)
            .map((x) => localName(x, language))
            .join(" ▸ ")}
          {chosen.node.serving_temp ? `  ·  ${chosen.node.serving_temp}` : ""}
        </Text>
      ) : (
        <Text style={styles.muted}>{t("wineForm.noType")}</Text>
      )}
      <BigButton
        label={t(chosen ? "wineForm.changeType" : "wineForm.chooseType")}
        icon="wine-outline"
        variant="secondary"
        onPress={() => setPicking(true)}
      />
      <CategoryPicker
        tree={asTree(types)}
        visible={picking}
        title={t("wineForm.chooseType")}
        onPick={(node) => {
          setCategoryId(node.id);
          setPicking(false);
        }}
        onClose={() => setPicking(false)}
      />

      <Chips
        label={t("wineForm.sweetness")}
        value={facets.sweetness}
        onChange={setFacet("sweetness")}
        options={facetOptions(options.sweetness)}
      />
      <Chips
        label={t("wineForm.body")}
        value={facets.body}
        onChange={setFacet("body")}
        options={facetOptions(options.body)}
      />
      <Chips
        label={t("wineForm.ageing")}
        value={facets.ageing}
        onChange={setFacet("ageing")}
        options={facetOptions(options.ageing)}
      />
      <PriceChoice
        label={t("wineForm.price")}
        value={facets.price_range}
        onChange={setFacet("price_range")}
      />
      <ShopPrice
        sourceUrl={orNull(texts.source)}
        sourceName={initial.source_name}
        sourcePrice={initial.source_price}
      />

      <SectionTitle text={t("wineForm.origin")} />
      <TextField
        label={t("wineForm.appellation")}
        hint={t("wineForm.appellationHint")}
        value={texts.appellation}
        onChangeText={setText("appellation")}
        autoCapitalize="words"
      />
      <TextField
        label={t("wineForm.grapes")}
        hint={t("wineForm.grapesHint")}
        value={texts.grapes}
        onChangeText={setText("grapes")}
        autoCapitalize="none"
      />
      <View style={styles.pair}>
        <View style={styles.cell}>
          <TextField
            label={t("wineForm.country")}
            hint={t("form.optional")}
            value={texts.country}
            onChangeText={setText("country")}
            autoCapitalize="words"
          />
        </View>
        <View style={styles.cell}>
          <TextField
            label={t("wineForm.vintage")}
            hint={t("form.optional")}
            value={texts.vintage}
            onChangeText={setText("vintage")}
            error={errors.vintage}
            keyboardType="number-pad"
            maxLength={4}
          />
        </View>
      </View>

      <SectionTitle text={t("wineForm.notes")} />
      <TextField
        label={t("wineForm.tasting")}
        hint={t("form.optional")}
        value={texts.tasting}
        onChangeText={setText("tasting")}
        multiline
        style={styles.multiline}
      />
      <TextField
        label={t("wineForm.pairing")}
        hint={t("wineForm.pairingHint")}
        value={texts.pairing}
        onChangeText={setText("pairing")}
        multiline
        style={styles.multiline}
      />
      <TextField
        label={t("wineForm.source")}
        hint={t("wineForm.sourceHint")}
        value={texts.source}
        onChangeText={setText("source")}
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
  chosen: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  muted: { fontSize: fontSize.body, color: colors.muted },
  pair: { flexDirection: "row", gap: spacing.s },
  cell: { flex: 1 },
  multiline: { minHeight: 110, paddingTop: spacing.s, textAlignVertical: "top" },
});
