/** Ficha de una especia (from a recipe ingredient or from the spice zone): what to use instead,
 * with the proportion and a note; how to make it at home if it is a blend; blends it is part of.
 * Substitutes and blends with a card of their own can be tapped. A blend can be edited (my
 * notebook's version), and my version can go back to the catalogue's (session 8). */
import { Ionicons } from "@expo/vector-icons";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { cap } from "../../components/SpiceRow.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { useSession } from "../../services/session.tsx";
import * as spices from "../../services/spices.ts";
import { useLoad } from "../../services/useLoad.ts";

export default function SpiceScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t, language } = useI18n();
  const { token } = useSession();
  const en = language !== "es";
  const data = useLoad(() => spices.card(Number(id), { language, token }), [id, language, token]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [editingPairs, setEditingPairs] = useState<string | null>(null); // the text being edited

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const card = data.data;
  const name = cap((en && card.name_en) || card.name);
  const blendNote = card.blend ? (en ? card.blend.note_en : card.blend.note_es) : null;
  const ownRow = card.blend?.notebook_blend_id ?? null; // my notebook's row, if any
  const ownNew = ownRow !== null && !card.is_own_version; // a blend of my own, not a version

  async function run(action: () => Promise<unknown>, thenBack: boolean) {
    if (!token) return;
    setBusy(true);
    setMessage(null);
    try {
      await action();
      if (thenBack) router.back();
      else await data.reload();
    } catch (error) {
      setMessage(errorText(error, t));
    } finally {
      setBusy(false);
    }
  }

  function confirm(title: string, text: string, button: string, action: () => void) {
    Alert.alert(title, text, [
      { text: t("common.cancel"), style: "cancel" },
      { text: button, style: "destructive", onPress: action },
    ]);
  }

  const auth = token ? { token, language } : null;

  function confirmRemove() {
    if (ownRow === null || !auth) return;
    const key = ownNew ? "delete" : "restore";
    confirm(t(`blend.${key}Title`), t(`blend.${key}Text`, { name }), t(`blend.${key}`), () =>
      run(() => spices.removeBlend(auth, ownRow), ownNew),
    );
  }

  function confirmRestoreSubstitutes() {
    if (!auth) return;
    confirm(t("subs.restoreTitle"), t("subs.restoreText", { name }), t("subs.restore"), () =>
      run(() => spices.clearSubstitutions(auth, card.id), false),
    );
  }

  function confirmRestorePairs() {
    if (!auth) return;
    confirm(t("pairs.restoreTitle"), t("pairs.restoreText", { name }), t("pairs.restore"), () =>
      run(() => spices.clearPairsWith(auth, card.id), false),
    );
  }

  async function savePairs() {
    if (!auth || editingPairs === null) return;
    const text = editingPairs.trim();
    if (!text) {
      setMessage(t("pairs.errorEmpty"));
      return;
    }
    await run(() => spices.setPairsWith(auth, card.id, text), false);
    setEditingPairs(null);
  }

  function confirmDeleteSpice() {
    if (!auth || card.notebook_spice_id === null) return;
    const spiceId = card.notebook_spice_id;
    confirm(t("ownSpice.deleteTitle"), t("ownSpice.deleteText", { name }), t("ownSpice.delete"), () =>
      run(() => spices.removeSpice(auth, spiceId), true),
    );
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: name }} />
      <Text style={styles.title} accessibilityRole="header">
        {name}
      </Text>
      {en ? (
        card.name_en ? (
          <Text style={styles.muted}>{t("spice.inSpanish", { name: card.name })}</Text>
        ) : null
      ) : card.aliases ? (
        <Text style={styles.muted}>{t("spice.aliases", { names: card.aliases })}</Text>
      ) : null}

      {card.notebook_spice_id !== null ? (
        <Text style={styles.mark}>
          {card.added_by ? t("recipes.addedBy", { name: card.added_by }) : t("ownSpice.mark")}
        </Text>
      ) : null}

      <SectionTitle text={t("pairs.title")} />
      {card.has_own_pairs_with ? (
        <Text style={styles.mark}>
          {card.pairs_with_added_by
            ? t("recipes.addedBy", { name: card.pairs_with_added_by })
            : t("pairs.mark")}
        </Text>
      ) : null}
      {editingPairs !== null ? (
        <View style={styles.actions}>
          <TextField
            label={t("pairs.field")}
            hint={t("pairs.fieldHint")}
            value={editingPairs}
            onChangeText={setEditingPairs}
            multiline
            autoCapitalize="none"
            style={styles.pairsField}
          />
          <BigButton label={t("pairs.save")} icon="checkmark" loading={busy} onPress={savePairs} />
          <BigButton
            label={t("common.cancel")}
            variant="link"
            onPress={() => setEditingPairs(null)}
          />
        </View>
      ) : (
        <>
          {card.pairs_with ? (
            <View style={styles.pairs}>
              {card.pairs_with.split(",").map((food, index) => {
                const label = food.trim();
                return label ? (
                  <View key={index} style={styles.pairChip}>
                    <Text style={styles.pairText}>{label}</Text>
                  </View>
                ) : null;
              })}
            </View>
          ) : (
            <Text style={styles.muted}>{t("pairs.none")}</Text>
          )}
          {token ? (
            <View style={styles.actions}>
              <BigButton
                label={t("pairs.edit")}
                icon="create-outline"
                variant="secondary"
                onPress={() => setEditingPairs(card.pairs_with ?? "")}
              />
              {card.has_own_pairs_with ? (
                <BigButton
                  label={t("pairs.restore")}
                  icon="refresh-outline"
                  variant="link"
                  loading={busy}
                  onPress={confirmRestorePairs}
                />
              ) : null}
            </View>
          ) : null}
        </>
      )}

      <SectionTitle text={t("spice.substitutes")} />
      {card.has_own_substitutions ? (
        <Text style={styles.mark}>
          {card.substitutions_added_by
            ? t("recipes.addedBy", { name: card.substitutions_added_by })
            : t("subs.mark")}
        </Text>
      ) : null}
      {card.substitutions.length ? (
        card.substitutions.map((s, index) => {
          const note = en ? s.note_en : s.note_es;
          const label = `${en ? s.substitute_en : s.substitute_es}${s.ratio ? `  (${s.ratio})` : ""}`;
          const target = s.substitute_id;
          const content = (
            <>
              <View style={styles.boxText}>
                <Text style={styles.strong}>{label}</Text>
                {note ? <Text style={styles.body}>{note}</Text> : null}
              </View>
              {target ? <Ionicons name="chevron-forward" size={24} color={colors.ink} /> : null}
            </>
          );
          return target && target !== card.id ? (
            <Pressable
              key={index}
              accessibilityRole="button"
              accessibilityLabel={label}
              onPress={() => router.push(`/spices/${target}`)}
              style={({ pressed }) => [styles.box, styles.boxRow, pressed && styles.pressed]}
            >
              {content}
            </Pressable>
          ) : (
            <View key={index} style={[styles.box, styles.boxRow]}>
              {content}
            </View>
          );
        })
      ) : (
        <Text style={styles.muted}>{t("spice.noSubstitutes")}</Text>
      )}
      {token ? (
        <View style={styles.actions}>
          <BigButton
            label={t("subs.edit")}
            icon="create-outline"
            variant="secondary"
            onPress={() => router.push({ pathname: "/spices/substitutions", params: { id } })}
          />
          {card.has_own_substitutions ? (
            <BigButton
              label={t("subs.restore")}
              icon="refresh-outline"
              variant="link"
              loading={busy}
              onPress={confirmRestoreSubstitutes}
            />
          ) : null}
        </View>
      ) : null}

      {card.blend ? (
        <>
          <SectionTitle text={t("spice.blend")} />
          {card.is_own_version ? (
            <Text style={styles.mark}>{t("blend.markVersion")}</Text>
          ) : ownNew ? (
            <Text style={styles.mark}>
              {card.added_by ? t("recipes.addedBy", { name: card.added_by }) : t("blend.markOwn")}
            </Text>
          ) : null}
          {card.blend.items.map((item) => (
            <Text key={item.ingredient_id} style={styles.body}>
              • {item.parts} {(en && item.name_en) || item.name}
              {item.is_optional ? ` ${t("spice.optional")}` : ""}
            </Text>
          ))}
          {blendNote ? <Text style={styles.muted}>{blendNote}</Text> : null}
          {token ? (
            <View style={styles.actions}>
              <BigButton
                label={t("blend.edit")}
                icon="create-outline"
                variant="secondary"
                onPress={() => router.push({ pathname: "/spices/blend", params: { id } })}
              />
              {ownRow !== null ? (
                <BigButton
                  label={t(ownNew ? "blend.delete" : "blend.restore")}
                  icon={ownNew ? "trash-outline" : "refresh-outline"}
                  variant="link"
                  loading={busy}
                  onPress={confirmRemove}
                />
              ) : null}
            </View>
          ) : null}
        </>
      ) : null}

      {card.used_in_blends.length ? (
        <>
          <SectionTitle text={t("spice.usedIn")} />
          {card.used_in_blends.map((b) => {
            const blendName = cap((en && b.name_en) || b.name);
            return (
              <Pressable
                key={b.ingredient_id}
                accessibilityRole="button"
                accessibilityLabel={blendName}
                onPress={() => router.push(`/spices/${b.ingredient_id}`)}
                style={({ pressed }) => [styles.box, styles.boxRow, pressed && styles.pressed]}
              >
                <Text style={[styles.strong, styles.boxText]}>{blendName}</Text>
                <Ionicons name="chevron-forward" size={24} color={colors.ink} />
              </Pressable>
            );
          })}
        </>
      ) : null}
      {token && card.notebook_spice_id !== null ? (
        <View style={styles.actions}>
          <SectionTitle text={t("ownSpice.section")} />
          <BigButton
            label={t("ownSpice.edit")}
            icon="create-outline"
            variant="secondary"
            onPress={() =>
              router.push({
                pathname: "/spices/spice",
                params: { id: String(card.notebook_spice_id), ingredient: id },
              })
            }
          />
          <BigButton
            label={t("ownSpice.delete")}
            icon="trash-outline"
            variant="link"
            loading={busy}
            onPress={confirmDeleteSpice}
          />
        </View>
      ) : null}
      <Message text={message} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  muted: { fontSize: fontSize.body, color: colors.muted },
  box: {
    gap: spacing.xs,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  mark: { fontSize: fontSize.small, fontWeight: "600", color: colors.muted },
  pairs: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  pairChip: {
    paddingHorizontal: spacing.m,
    paddingVertical: spacing.s,
    borderRadius: radius.l,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  pairText: { fontSize: fontSize.body, color: colors.ink },
  pairsField: { minHeight: 96, paddingTop: spacing.s, textAlignVertical: "top" },
  actions: { gap: spacing.s, marginTop: spacing.s },
  boxRow: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  boxText: { flex: 1, gap: spacing.xs },
  pressed: { opacity: 0.7 },
  strong: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  body: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
});
