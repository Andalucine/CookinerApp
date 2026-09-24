/**
 * Preparar el menú (session 9): "¿Qué te apetece comer esta semana?" (foods, optional), which
 * meals of the day, what the notebook can offer (and the warning when there are no
 * breakfast recipes), and "Hacer el borrador". Never the word "diet" (decision, session 8).
 */
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { ToggleChips } from "../../components/ToggleChips.tsx";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as menus from "../../services/menu.ts";
import { useLoad } from "../../services/useLoad.ts";
import { MEALS, mondayOf, today, weekLabel } from "../../services/week.ts";

function Setup({ auth, week }: { auth: Auth; week: string }) {
  const { t, language } = useI18n();
  const check = useLoad(() => menus.check(auth, week), [auth.token, auth.language, week]);
  const [wants, setWants] = useState("");
  const [meals, setMeals] = useState<number[]>([1, 2]); // lunch and dinner on by default
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (check.loading && !check.data) return <Loading />;
  if (check.error || !check.data) {
    return (
      <Screen>
        <LoadError error={check.error} onRetry={check.reload} />
      </Screen>
    );
  }
  const info = check.data;
  const chosen = MEALS.filter((_, i) => meals.includes(i));

  async function makeDraft() {
    if (!chosen.length) {
      setMessage(t("menu.errorMeals"));
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await menus.draft(auth, week, chosen, wants.trim() || null);
      router.dismissTo({ pathname: "/menu", params: { week } });
    } catch (error) {
      setMessage(errorText(error, t));
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.week}>{weekLabel(week, language)}</Text>
      <TextField
        label={t("menu.wants")}
        hint={t("menu.wantsHint")}
        value={wants}
        onChangeText={setWants}
        autoCapitalize="none"
        multiline
        style={styles.wants}
      />
      <ToggleChips
        label={t("menu.meals")}
        options={MEALS.map((meal, i) => ({ value: i, label: t(`menu.meal.${meal}` as TextKey) }))}
        perRow={3}
        selected={meals}
        onToggle={(i) => setMeals((m) => (m.includes(i) ? m.filter((x) => x !== i) : [...m, i]))}
      />
      <View style={styles.info}>
        <Text style={styles.muted}>
          {t("menu.recipesNote", {
            total: info.total_recipes,
            breakfast: info.breakfast_recipes,
            main: info.main_recipes,
          })}
        </Text>
        {info.total_recipes === 0 ? <Text style={styles.warn}>{t("menu.noRecipes")}</Text> : null}
        {meals.includes(0) && info.breakfast_recipes === 0 && info.total_recipes > 0 ? (
          <Text style={styles.warn}>{t("menu.noBreakfast")}</Text>
        ) : null}
      </View>
      <Message text={message} />
      <BigButton
        label={t("menu.draft")}
        icon="calendar-outline"
        loading={busy}
        disabled={info.total_recipes === 0}
        onPress={makeDraft}
      />
      <Text style={styles.muted}>{t("menu.draftHint")}</Text>
    </Screen>
  );
}

export default function SetupScreen() {
  const params = useLocalSearchParams<{ week?: string }>();
  const valid = params.week && /^\d{4}-\d{2}-\d{2}$/.test(params.week);
  const week = mondayOf(valid ? params.week! : today());
  return <SignedIn>{(auth) => <Setup auth={auth} week={week} />}</SignedIn>;
}

const styles = StyleSheet.create({
  week: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  // Several lines: the foods wrap instead of scrolling sideways (Beatriz, session 9)
  wants: { minHeight: 96, paddingTop: spacing.s, textAlignVertical: "top" },
  info: { gap: spacing.xs },
  muted: { fontSize: fontSize.small, color: colors.muted },
  warn: { fontSize: fontSize.body, color: colors.ink },
});
