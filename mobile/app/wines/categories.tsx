/**
 * Por tipos: Tintos · Blancos · Rosados · Espumosos… with the number of wines; inside, the
 * subtypes (Tinto joven, Crianza…) with "Todos los…" first. Same look as recipe categories.
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { countLookup } from "../../services/categoryTree.ts";
import { localName } from "../../services/format.ts";
import { useLoad } from "../../services/useLoad.ts";
import * as wines from "../../services/wines.ts";

function WineTypes({ auth, parentId }: { auth: Auth; parentId: number | null }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [tree, counts] = await Promise.all([
      wines.wineCategories(auth.language),
      wines.categoryCounts(auth),
    ]);
    return { tree, count: countLookup(counts) };
  }, [auth.token, auth.language]);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const { tree, count } = data.data;
  const parent = parentId ? tree.find((n) => n.id === parentId) ?? null : null;
  const children = parent ? parent.children : tree;
  const name = (node: wines.WineCategoryNode) => localName(node, language);

  function openList(node: wines.WineCategoryNode) {
    router.push({
      pathname: "/wines/list",
      params: { category_id: String(node.id), title: name(node) },
    });
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: parent ? name(parent) : t("wines.byType") }} />
      <Text style={styles.intro}>{t("wines.typesIntro")}</Text>
      <View style={styles.list}>
        {parent ? (
          <RowButton
            label={t("categories.allOf", { name: name(parent) })}
            count={count(parent.id)}
            strong
            onPress={() => openList(parent)}
          />
        ) : null}
        {children.map((node) => (
          <RowButton
            key={node.id}
            label={node.serving_temp && parent ? `${name(node)} · ${node.serving_temp}` : name(node)}
            count={count(node.id)}
            strong={!parent}
            muted={count(node.id) === 0}
            onPress={() =>
              node.children.length
                ? router.push({ pathname: "/wines/categories", params: { parent: String(node.id) } })
                : openList(node)
            }
          />
        ))}
      </View>
    </Screen>
  );
}

export default function WineTypesScreen() {
  const { parent } = useLocalSearchParams<{ parent?: string }>();
  const parentId = parent ? Number(parent) : null;
  return <SignedIn>{(auth) => <WineTypes auth={auth} parentId={parentId} />}</SignedIn>;
}

const styles = StyleSheet.create({
  list: { gap: spacing.s },
  intro: { fontSize: fontSize.body, color: colors.muted },
});
