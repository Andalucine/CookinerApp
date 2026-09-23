/**
 * Choosing the category of a recipe: a full screen over the form, one level at a time
 * (Salado → Pescados → Guisos de pescado), like the category tree. Any level can be chosen.
 * It keeps the look of every other screen (session 7): "Volver" on the left (one level up, or
 * back to the form), the title in the middle and the anagram on the right.
 */
import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useI18n } from "../i18n";
import { type CategoryNode, findCategory } from "../services/categoryTree.ts";
import { localName } from "../services/format.ts";
import { HomeLogo } from "./HomeLogo.tsx";
import { RowButton } from "./RowButton.tsx";
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

  function back() {
    if (!found) return close();
    setParentId(found.path.length > 1 ? found.path[found.path.length - 2].id : null);
  }

  function pick(node: CategoryNode) {
    setParentId(null);
    onPick(node);
  }

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={back}>
      <SafeAreaView style={styles.safe} edges={["top", "bottom", "left", "right"]}>
        <View style={styles.header}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("common.back")}
            onPress={back}
            hitSlop={8}
            style={({ pressed }) => [styles.back, pressed && styles.pressed]}
          >
            <Ionicons name="chevron-back" size={26} color={colors.ink} />
            <Text style={styles.backText}>{t("common.back")}</Text>
          </Pressable>
          <Text style={styles.headerTitle} numberOfLines={1} accessibilityRole="header">
            {found ? name(found.node) : t("form.chooseCategory")}
          </Text>
          <View style={styles.logo}>
            <HomeLogo size={36} />
          </View>
        </View>
        <ScrollView contentContainerStyle={styles.content}>
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
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 56,
    paddingHorizontal: spacing.m,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  back: { flexDirection: "row", alignItems: "center", minWidth: 96, minHeight: 44 },
  backText: { fontSize: fontSize.body, color: colors.ink },
  pressed: { opacity: 0.6 },
  headerTitle: {
    flex: 1,
    textAlign: "center",
    fontSize: 20,
    fontWeight: "700",
    color: colors.ink,
  },
  logo: { minWidth: 96, alignItems: "flex-end" },
  content: { padding: spacing.l, gap: spacing.m },
  path: { fontSize: fontSize.body, fontWeight: "600", color: colors.muted },
  list: { gap: spacing.s },
});
