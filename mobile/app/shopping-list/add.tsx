/**
 * Elegir qué añadir a la compra (session 9): the ingredients of a recipe (?recipe=) or of
 * the week's menu (?menu=), each with a tick. What is missing comes ticked; what is in the
 * pantry, already on the list or taken for granted comes unticked but can be ticked too.
 * "Todos" / "Ninguno" and "Añadir N a la compra".
 */
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing, touchHeight } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { defaultTicks } from "../../services/kitchen.ts";
import * as menus from "../../services/menu.ts";
import * as shopping from "../../services/shopping.ts";
import { useLoad } from "../../services/useLoad.ts";

type Source = { recipe?: number; menu?: number };

function AddFrom({ auth, source, title }: { auth: Auth; source: Source; title: string }) {
  const { t } = useI18n();
  const rows = useLoad(
    async () => {
      const list = source.menu
        ? await menus.missingForWeek(auth, source.menu)
        : await shopping.missingForRecipe(auth, source.recipe!);
      setTicked(new Set(defaultTicks(list)));
      return list;
    },
    [auth.token, auth.language, source.recipe, source.menu],
  );
  const [ticked, setTicked] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (rows.loading && !rows.data) return <Loading />;
  if (rows.error || !rows.data) {
    return (
      <Screen>
        <LoadError error={rows.error} onRetry={rows.reload} />
      </Screen>
    );
  }
  const list = rows.data;

  function toggle(id: number) {
    setTicked((before) => {
      const next = new Set(before);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function add() {
    const ids = [...ticked];
    if (!ids.length) return;
    setBusy(true);
    setMessage(null);
    try {
      if (source.menu) await menus.shopping(auth, source.menu, ids);
      else await shopping.fromRecipe(auth, source.recipe!, ids);
      router.replace("/shopping-list");
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  return (
    <Screen>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      {list.length ? (
        <>
          <Text style={styles.hint}>{t("addMissing.hint")}</Text>
          <View style={styles.row}>
            <BigButton
              label={t("addMissing.all")}
              variant="link"
              onPress={() => setTicked(new Set(list.map((r) => r.ingredient_id)))}
            />
            <BigButton
              label={t("addMissing.none")}
              variant="link"
              onPress={() => setTicked(new Set())}
            />
          </View>
          <View style={styles.list}>
            {list.map((row) => {
              const on = ticked.has(row.ingredient_id);
              const why =
                row.status === "missing" ? null : t(`addMissing.${row.status}` as TextKey);
              return (
                <Pressable
                  key={row.ingredient_id}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: on }}
                  accessibilityLabel={[row.name, row.quantity, why].filter(Boolean).join(", ")}
                  onPress={() => toggle(row.ingredient_id)}
                  style={({ pressed }) => [
                    styles.item,
                    on && styles.itemOn,
                    pressed && styles.pressed,
                  ]}
                >
                  <Ionicons
                    name={on ? "checkbox" : "square-outline"}
                    size={30}
                    color={colors.ink}
                  />
                  <View style={styles.text}>
                    <Text style={[styles.name, !on && styles.nameOff]}>{row.name}</Text>
                    {row.quantity ? <Text style={styles.detail}>{row.quantity}</Text> : null}
                    {why ? <Text style={styles.why}>{why}</Text> : null}
                    {source.menu && row.recipes.length ? (
                      <Text style={styles.detail}>{row.recipes.join(" · ")}</Text>
                    ) : null}
                  </View>
                </Pressable>
              );
            })}
          </View>
          <Message text={message} />
          <BigButton
            label={t("addMissing.add", { count: ticked.size })}
            icon="cart-outline"
            loading={busy}
            disabled={!ticked.size}
            onPress={add}
          />
        </>
      ) : (
        <Text style={styles.hint}>{t("addMissing.empty")}</Text>
      )}
    </Screen>
  );
}

export default function AddFromScreen() {
  const params = useLocalSearchParams<{ recipe?: string; menu?: string; title?: string }>();
  const source: Source = params.menu
    ? { menu: Number(params.menu) }
    : { recipe: Number(params.recipe) };
  return (
    <SignedIn>
      {(auth) => <AddFrom auth={auth} source={source} title={params.title ?? ""} />}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  hint: { fontSize: fontSize.small, color: colors.muted },
  row: { flexDirection: "row", gap: spacing.m },
  list: { gap: spacing.s },
  item: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    minHeight: touchHeight,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  itemOn: { borderColor: colors.accent, backgroundColor: colors.accentSoft },
  pressed: { opacity: 0.7 },
  text: { flex: 1, gap: 2 },
  name: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  nameOff: { fontWeight: "400" },
  detail: { fontSize: fontSize.small, color: colors.muted },
  why: { fontSize: fontSize.small, color: colors.ink, fontStyle: "italic" },
});
