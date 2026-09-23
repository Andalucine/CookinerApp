/**
 * Choosing the category of a recipe: a full screen over the form, one level at a time
 * (Salado → Pescados → Guisos de pescado), like the category tree. Any level can be chosen.
 */
import { useState } from "react";
import { Modal, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { type CategoryNode, findCategory } from "../services/categoryTree.ts";
import { localName } from "../services/format.ts";
import { BigButton } from "./BigButton.tsx";
import { RowButton } from "./RowButton.tsx";
import { Screen } from "./Screen.tsx";
import { colors, fontSize, spacing } from "./theme.ts";

export function CategoryPicker({
  tree,
  visible,
  onPick,
  onClose,
}: {
  tree: CategoryNode[];
  visible: boolean;
  onPick: (node: CategoryNode) => void;
  onClose: () => void;
}) {
  const { t, language } = useI18n();
  const [parentId, setParentId] = useState<number | null>(null);
  const found = parentId ? findCategory(tree, parentId) : null;
  const children = found ? found.node.children : tree;
  const name = (node: CategoryNode) => localName(node, language);

  function close() {
    setParentId(null);
    onClose();
  }

  function pick(node: CategoryNode) {
    setParentId(null);
    onPick(node);
  }

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={close}>
      <Screen>
        <Text style={styles.title}>{t("form.chooseCategory")}</Text>
        {found ? <Text style={styles.path}>{found.path.map(name).join(" ▸ ")}</Text> : null}
        <View style={styles.list}>
          {found ? (
            <RowButton
              label={t("form.thisCategory", { name: name(found.node) })}
              icon="checkmark"
              strong
              onPress={() => pick(found.node)}
            />
          ) : null}
          {children.map((node) => (
            <RowButton
              key={node.id}
              label={name(node)}
              onPress={() => (node.children.length ? setParentId(node.id) : pick(node))}
            />
          ))}
        </View>
        {found ? (
          <BigButton
            label={t("common.back")}
            icon="arrow-back"
            variant="secondary"
            onPress={() =>
              setParentId(found.path.length > 1 ? found.path[found.path.length - 2].id : null)
            }
          />
        ) : null}
        <BigButton label={t("common.cancel")} variant="link" onPress={close} />
      </Screen>
    </Modal>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  path: { fontSize: fontSize.body, fontWeight: "600", color: colors.muted },
  list: { gap: spacing.s },
});
