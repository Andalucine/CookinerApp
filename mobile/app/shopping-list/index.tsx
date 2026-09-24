/**
 * Lista de la compra (session 9): a field to add things one by one (each goes to its section
 * by itself), how many are left, and the sections in supermarket order. A tap ticks a line as
 * bought; ⋯ opens its options: move it to another section (the notebook remembers it for that
 * ingredient), put a photo of the product on it (session 9: to buy just that brand) or delete
 * it; the photo's thumbnail sits before the text. "Quitar lo comprado" asks whether to note it
 * in the pantry.
 * Always my own notebook.
 */
import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { AddField } from "../../components/AddField.tsx";
import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { PhotoButton, PhotoThumb } from "../../components/Photo.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing, touchHeight } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { localName } from "../../services/format.ts";
import { boughtCount, shoppingLine, withChecked } from "../../services/kitchen.ts";
import * as shopping from "../../services/shopping.ts";
import { useLoad } from "../../services/useLoad.ts";

function ShoppingList({ auth }: { auth: Auth }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [list, sections] = await Promise.all([
      shopping.get(auth),
      shopping.sections(auth.language),
    ]);
    return { list, sections };
  }, [auth.token, auth.language]);
  const [open, setOpen] = useState<number | null>(null); // the line whose options are shown
  const [message, setMessage] = useState<{ text: string; kind: "error" | "ok" } | null>(null);
  const [clearing, setClearing] = useState(false);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const { list, sections } = data.data;
  const bought = boughtCount(list);
  const fail = (error: unknown) => setMessage({ text: errorText(error, t), kind: "error" });

  async function add(text: string) {
    const line = shoppingLine(text);
    if (!line) return;
    setMessage(null);
    try {
      await shopping.add(auth, line.text, line.name);
      await data.reload();
    } catch (error) {
      fail(error);
      throw error;
    }
  }

  async function toggle(item: shopping.ShoppingItem) {
    const on = !item.is_checked;
    data.setData({ list: withChecked(list, item.id, on), sections });
    try {
      await shopping.setChecked(auth, item.id, on);
    } catch (error) {
      fail(error);
      data.reload();
    }
  }

  async function move(item: shopping.ShoppingItem, code: string) {
    setOpen(null);
    try {
      await shopping.move(auth, item.id, code);
      await data.reload();
    } catch (error) {
      fail(error);
    }
  }

  async function setPhoto(item: shopping.ShoppingItem, url: string | null) {
    try {
      await shopping.setPhoto(auth, item.id, url);
      await data.reload();
    } catch (error) {
      fail(error);
    }
  }

  async function remove(item: shopping.ShoppingItem) {
    setOpen(null);
    try {
      await shopping.remove(auth, item.id);
      await data.reload();
    } catch (error) {
      fail(error);
    }
  }

  async function clear(toPantry: boolean) {
    setClearing(true);
    setMessage(null);
    try {
      const answer = await shopping.clearChecked(auth, toPantry);
      setMessage({ text: answer.message, kind: "ok" });
      await data.reload();
    } catch (error) {
      fail(error);
    } finally {
      setClearing(false);
    }
  }

  function askClear() {
    Alert.alert(t("shopping.clearTitle"), t("shopping.clearText"), [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("shopping.clearNo"), onPress: () => clear(false) },
      { text: t("shopping.clearYes"), onPress: () => clear(true) },
    ]);
  }

  return (
    <Screen>
      <AddField label={t("shopping.add")} hint={t("shopping.addHint")} onAdd={add} />
      <Message text={message?.text ?? null} kind={message?.kind} />
      {list.total ? (
        <Text style={styles.summary}>
          {list.pending ? t("shopping.pending", { count: list.pending }) : t("shopping.allBought")}
        </Text>
      ) : (
        <Text style={styles.muted}>{t("shopping.empty")}</Text>
      )}

      {list.sections.map((section) => (
        <View key={section.code} style={styles.section}>
          <SectionTitle text={localName(section, language)} />
          {section.code === "other" ? (
            <Text style={styles.muted}>{t("shopping.otherHint")}</Text>
          ) : null}
          {section.items.map((item) => (
            <View key={item.id} style={styles.itemBox}>
              <View style={styles.item}>
                <Pressable
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: item.is_checked }}
                  accessibilityLabel={item.text}
                  onPress={() => toggle(item)}
                  style={({ pressed }) => [styles.line, pressed && styles.pressed]}
                >
                  <Ionicons
                    name={item.is_checked ? "checkbox" : "square-outline"}
                    size={30}
                    color={item.is_checked ? colors.muted : colors.ink}
                  />
                  <PhotoThumb url={item.image_url} size={44} label={item.text} />
                  <Text style={[styles.text, item.is_checked && styles.bought]}>
                    {item.text}
                    {item.quantity && item.quantity !== item.text ? (
                      <Text style={styles.quantity}>{`  ${item.quantity}`}</Text>
                    ) : null}
                  </Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={t("shopping.options", { text: item.text })}
                  onPress={() => setOpen(open === item.id ? null : item.id)}
                  hitSlop={8}
                  style={({ pressed }) => [styles.more, pressed && styles.pressed]}
                >
                  <Ionicons name="ellipsis-horizontal" size={26} color={colors.ink} />
                </Pressable>
              </View>
              {open === item.id ? (
                <View style={styles.options}>
                  <Chips
                    label={t("shopping.moveTo")}
                    options={sections.map((s) => ({
                      value: s.code,
                      label: localName(s, language),
                    }))}
                    value={section.code}
                    onChange={(code) => move(item, code)}
                  />
                  <PhotoButton
                    auth={auth}
                    url={item.image_url}
                    onChange={(url) => setPhoto(item, url)}
                    compact
                  />
                  <BigButton
                    label={t("shopping.delete")}
                    icon="trash-outline"
                    variant="secondary"
                    onPress={() => remove(item)}
                  />
                  <BigButton
                    label={t("shopping.close")}
                    variant="link"
                    onPress={() => setOpen(null)}
                  />
                </View>
              ) : null}
            </View>
          ))}
        </View>
      ))}

      {bought ? (
        <View style={styles.clear}>
          <BigButton
            label={t("shopping.clear", { count: bought })}
            icon="checkmark-done-outline"
            variant="secondary"
            loading={clearing}
            onPress={askClear}
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function ShoppingListScreen() {
  return <SignedIn>{(auth) => <ShoppingList auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  summary: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  muted: { fontSize: fontSize.small, color: colors.muted },
  section: { gap: spacing.s },
  itemBox: { borderRadius: radius.m, borderWidth: 2, borderColor: colors.border },
  item: { flexDirection: "row", alignItems: "center" },
  line: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    minHeight: touchHeight,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
  },
  text: { flex: 1, fontSize: fontSize.body, color: colors.ink },
  bought: { color: colors.muted, textDecorationLine: "line-through" },
  quantity: { fontSize: fontSize.small, color: colors.muted },
  more: { minHeight: touchHeight, paddingHorizontal: spacing.m, justifyContent: "center" },
  pressed: { opacity: 0.7 },
  options: { gap: spacing.s, padding: spacing.m, borderTopWidth: 2, borderColor: colors.border },
  clear: { marginTop: spacing.l },
});
