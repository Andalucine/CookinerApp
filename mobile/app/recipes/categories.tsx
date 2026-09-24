/**
 * Categorías: the tree Salado · Dulce · Bebidas, one level per screen with big rows and the
 * number of recipes. A category with subcategories opens the next level (with "Todas las
 * recetas de…" first); one without opens the list. Also for someone else's notebook.
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { LoadError, Loading } from "../../components/LoadState.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import * as catalog from "../../services/catalog.ts";
import { type CategoryNode, countLookup, findCategory } from "../../services/categoryTree.ts";
import { localName } from "../../services/format.ts";
import * as recipes from "../../services/recipes.ts";
import { notebookParams, type OtherNotebook, readNotebook } from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function Categories({
  auth,
  parentId,
  notebook,
}: {
  auth: Auth;
  parentId: number | null;
  notebook: OtherNotebook | null;
}) {
  const { t, language } = useI18n();
  const carry = notebookParams(notebook);
  const data = useLoad(async () => {
    const [tree, counts] = await Promise.all([
      catalog.categories(auth.language),
      recipes.categoryCounts(auth, notebook?.id),
    ]);
    return { tree, count: countLookup(counts) };
  }, [auth.token, auth.language, notebook?.id]);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }

  const { tree, count } = data.data;
  const found = parentId ? findCategory(tree, parentId) : null;
  const children: CategoryNode[] = found ? found.node.children : tree;
  const name = (node: CategoryNode) => localName(node, language);

  function open(node: CategoryNode) {
    if (node.children.length) {
      router.push({ pathname: "/recipes/categories", params: { ...carry, parent: String(node.id) } });
    } else {
      router.push({
        pathname: "/recipes/list",
        params: { ...carry, category_id: String(node.id), title: name(node) },
      });
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: found ? name(found.node) : t("categories.title") }} />
      <NotebookBanner notebook={notebook} />
      {found ? (
        <Text style={styles.path}>{found.path.map(name).join(" ▸ ")}</Text>
      ) : (
        <Text style={styles.intro}>
          {notebook ? t("categories.introShared") : t("categories.intro")}
        </Text>
      )}
      <View style={styles.list}>
        {found ? (
          <RowButton
            label={t("categories.allOf", { name: name(found.node) })}
            count={count(found.node.id)}
            strong
            onPress={() =>
              router.push({
                pathname: "/recipes/list",
                params: {
                  ...carry,
                  category_id: String(found.node.id),
                  title: name(found.node),
                },
              })
            }
          />
        ) : null}
        {children.map((node) => (
          <RowButton
            key={node.id}
            label={name(node)}
            count={count(node.id)}
            strong={!found}
            muted={count(node.id) === 0}
            onPress={() => open(node)}
          />
        ))}
      </View>
    </Screen>
  );
}

export default function CategoriesScreen() {
  const params = useLocalSearchParams<{ parent?: string }>();
  const parentId = params.parent ? Number(params.parent) : null;
  const notebook = readNotebook(params);
  return (
    <SignedIn>
      {(auth) => <Categories auth={auth} parentId={parentId} notebook={notebook} />}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.s },
  path: { fontSize: fontSize.body, fontWeight: "600", color: colors.muted },
  intro: { fontSize: fontSize.body, color: colors.muted },
});
