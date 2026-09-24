/**
 * Menú de la semana (session 9): the week (previous / this / next), and for each day its
 * meals with the recipe proposed. Tapping a plate opens its options: another proposal,
 * choose from my recipes, write by hand, leave empty, see the recipe. At the bottom, "Añadir
 * lo que falta para toda la semana" to the shopping list, and "Empezar de nuevo". Without a
 * menu for the week: a button to plan it. Always my own notebook.
 */
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing, touchHeight } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { ApiError } from "../../services/apiClient.ts";
import { errorText } from "../../services/errors.ts";
import * as menus from "../../services/menu.ts";
import { useLoad } from "../../services/useLoad.ts";
import {
  dayName,
  isThisWeek,
  mondayOf,
  shiftWeek,
  slotsOfDay,
  today,
  weekLabel,
  withSlot,
} from "../../services/week.ts";

async function menuOrNothing(auth: Auth, week: string) {
  try {
    return await menus.get(auth, week);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

function Week({ auth, week }: { auth: Auth; week: string }) {
  const { t, language } = useI18n();
  const data = useLoad(() => menuOrNothing(auth, week), [auth.token, auth.language, week]);
  const [open, setOpen] = useState<number | null>(null); // the slot with its options shown
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; kind: "ok" | "error" } | null>(null);
  const fail = (error: unknown) => setMessage({ text: errorText(error, t), kind: "error" });

  const go = (target: string) => router.setParams({ week: target });

  if (data.loading && data.data === null && !data.error) return <Loading />;
  if (data.error) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const menu = data.data;
  const mealName = (meal: menus.Meal) => t(`menu.meal.${meal}` as TextKey);

  async function update(slot: menus.Slot, action: () => Promise<menus.Slot>) {
    if (!menu) return;
    setBusy(true);
    setMessage(null);
    try {
      const changed = await action();
      data.setData({ ...menu, slots: withSlot(menu.slots, changed) });
      setOpen(null);
      setNote("");
    } catch (error) {
      fail(error);
    } finally {
      setBusy(false);
    }
  }

  async function addShopping() {
    if (!menu) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await menus.shopping(auth, menu.id);
      setMessage({
        kind: "ok",
        text: result.added.length
          ? t("menu.shoppingDone", { names: result.added.map((i) => i.text).join(", ") })
          : t("menu.shoppingNone"),
      });
    } catch (error) {
      fail(error);
    } finally {
      setBusy(false);
    }
  }

  function confirmRemake() {
    Alert.alert(t("menu.remakeTitle"), t("menu.remakeText"), [
      { text: t("common.cancel"), style: "cancel" },
      {
        text: t("menu.remake"),
        style: "destructive",
        onPress: () => router.push({ pathname: "/menu/setup", params: { week } }),
      },
    ]);
  }

  return (
    <Screen>
      <View style={styles.weekRow}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("menu.prevWeek")}
          onPress={() => go(shiftWeek(week, -1))}
          style={styles.arrow}
        >
          <Ionicons name="chevron-back" size={28} color={colors.ink} />
        </Pressable>
        <View style={styles.weekText}>
          {isThisWeek(week) ? <Text style={styles.thisWeek}>{t("menu.thisWeek")}</Text> : null}
          <Text style={styles.weekLabel}>{weekLabel(week, language)}</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("menu.nextWeek")}
          onPress={() => go(shiftWeek(week, 1))}
          style={styles.arrow}
        >
          <Ionicons name="chevron-forward" size={28} color={colors.ink} />
        </Pressable>
      </View>

      {!menu ? (
        <>
          <Text style={styles.body}>{t("menu.none")}</Text>
          <BigButton
            label={t("menu.make")}
            icon="calendar-outline"
            onPress={() => router.push({ pathname: "/menu/setup", params: { week } })}
          />
        </>
      ) : (
        <>
          {menu.wants ? (
            <Text style={styles.muted}>
              {t("menu.wants")} {menu.wants}
            </Text>
          ) : null}
          {menu.notices.map((notice) => (
            <Text key={notice} style={styles.notice}>
              {t(`menu.notice.${notice}` as TextKey)}
            </Text>
          ))}
          <Message text={message?.text ?? null} kind={message?.kind} />

          {[0, 1, 2, 3, 4, 5, 6].map((day) => (
            <View key={day} style={styles.day}>
              <Text style={styles.dayName} accessibilityRole="header">
                {dayName(day, language)}
              </Text>
              {slotsOfDay(menu.slots, day).map((slot) => {
                const label = slot.recipe?.title ?? slot.note ?? t("menu.empty");
                return (
                  <View key={slot.id} style={[styles.slotBox, open === slot.id && styles.slotOpen]}>
                    <Pressable
                      accessibilityRole="button"
                      accessibilityLabel={`${mealName(slot.meal)}: ${label}`}
                      onPress={() => {
                        setOpen(open === slot.id ? null : slot.id);
                        setNote(slot.note ?? "");
                      }}
                      style={({ pressed }) => [styles.slot, pressed && styles.pressed]}
                    >
                      <Text style={styles.mealName}>{mealName(slot.meal)}</Text>
                      <Text
                        style={[styles.plate, !slot.recipe && !slot.note && styles.plateEmpty]}
                        numberOfLines={2}
                      >
                        {label}
                      </Text>
                      <Ionicons
                        name={open === slot.id ? "chevron-up" : "chevron-down"}
                        size={22}
                        color={colors.ink}
                      />
                    </Pressable>
                    {open === slot.id ? (
                      <View style={styles.options}>
                        {slot.recipe ? (
                          <BigButton
                            label={t("menu.open")}
                            icon="book-outline"
                            variant="link"
                            onPress={() => router.push(`/recipes/${slot.recipe!.id}`)}
                          />
                        ) : null}
                        <BigButton
                          label={t("menu.another")}
                          icon="shuffle-outline"
                          variant="secondary"
                          loading={busy}
                          onPress={() => update(slot, () => menus.another(auth, menu.id, slot.id))}
                        />
                        <BigButton
                          label={t("menu.choose")}
                          icon="search"
                          variant="secondary"
                          onPress={() =>
                            router.push({
                              pathname: "/menu/pick",
                              params: {
                                menu: String(menu.id),
                                slot: String(slot.id),
                                title: t("menu.pickFor", {
                                  day: dayName(day, language),
                                  meal: mealName(slot.meal),
                                }),
                              },
                            })
                          }
                        />
                        <TextField
                          label={t("menu.write")}
                          hint={t("menu.writeHint")}
                          value={note}
                          onChangeText={setNote}
                          onSubmitEditing={() =>
                            update(slot, () =>
                              menus.setSlot(auth, menu.id, slot.id, {
                                recipe_id: null,
                                note: note.trim() || null,
                              }),
                            )
                          }
                          returnKeyType="done"
                        />
                        {note.trim() && note.trim() !== (slot.note ?? "") ? (
                          <BigButton
                            label={t("form.saveChanges")}
                            icon="checkmark"
                            loading={busy}
                            onPress={() =>
                              update(slot, () =>
                                menus.setSlot(auth, menu.id, slot.id, {
                                  recipe_id: null,
                                  note: note.trim(),
                                }),
                              )
                            }
                          />
                        ) : null}
                        {slot.recipe || slot.note ? (
                          <BigButton
                            label={t("menu.clear")}
                            icon="remove-circle-outline"
                            variant="link"
                            onPress={() =>
                              update(slot, () =>
                                menus.setSlot(auth, menu.id, slot.id, {
                                  recipe_id: null,
                                  note: null,
                                }),
                              )
                            }
                          />
                        ) : null}
                        <BigButton
                          label={t("menu.close")}
                          variant="link"
                          onPress={() => setOpen(null)}
                        />
                      </View>
                    ) : null}
                  </View>
                );
              })}
            </View>
          ))}

          <View style={styles.actions}>
            <BigButton
              label={t("menu.shopping")}
              icon="cart-outline"
              loading={busy}
              onPress={addShopping}
            />
            <BigButton
              label={t("menu.remake")}
              icon="refresh"
              variant="secondary"
              onPress={confirmRemake}
            />
          </View>
        </>
      )}
    </Screen>
  );
}

export default function MenuScreen() {
  const params = useLocalSearchParams<{ week?: string }>();
  const valid = params.week && /^\d{4}-\d{2}-\d{2}$/.test(params.week);
  const week = mondayOf(valid ? params.week! : today());
  return <SignedIn>{(auth) => <Week auth={auth} week={week} />}</SignedIn>;
}

const styles = StyleSheet.create({
  weekRow: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  arrow: {
    width: touchHeight,
    height: touchHeight,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  weekText: { flex: 1, alignItems: "center", gap: 2 },
  thisWeek: { fontSize: fontSize.small, fontWeight: "700", color: colors.muted },
  weekLabel: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink, textAlign: "center" },
  body: { fontSize: fontSize.body, color: colors.ink },
  muted: { fontSize: fontSize.small, color: colors.muted },
  notice: { fontSize: fontSize.small, color: colors.ink, fontStyle: "italic" },
  day: { gap: spacing.xs },
  dayName: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink, marginTop: spacing.s },
  slotBox: { borderRadius: radius.m, borderWidth: 2, borderColor: colors.border },
  slotOpen: { borderColor: colors.ink, backgroundColor: colors.accentSoft },
  slot: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    minHeight: touchHeight,
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
  },
  pressed: { opacity: 0.7 },
  mealName: { width: 84, fontSize: fontSize.small, fontWeight: "700", color: colors.muted },
  plate: { flex: 1, fontSize: fontSize.body, color: colors.ink },
  plateEmpty: { color: colors.muted, fontStyle: "italic" },
  options: { gap: spacing.s, padding: spacing.m, borderTopWidth: 2, borderColor: colors.border },
  actions: { marginTop: spacing.l, gap: spacing.s },
});
