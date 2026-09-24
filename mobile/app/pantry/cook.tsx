/**
 * ¿Qué puedo cocinar? (session 9): the recipes of my notebook I can make with what I have,
 * and those one ingredient short, with "Te falta: pimentón" and a button to put it on the
 * shopping list.
 */
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RecipeCard } from "../../components/RecipeCard.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as pantry from "../../services/pantry.ts";
import * as shopping from "../../services/shopping.ts";
import { useLoad } from "../../services/useLoad.ts";

function Cook({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const data = useLoad(() => pantry.whatCanICook(auth), [auth.token, auth.language]);
  const [added, setAdded] = useState<Set<number>>(new Set());
  const [message, setMessage] = useState<string | null>(null);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const { complete, missing_one } = data.data;

  async function addToList(ingredientId: number, name: string) {
    setMessage(null);
    try {
      await shopping.add(auth, name, name);
      setAdded((before) => new Set(before).add(ingredientId));
    } catch (error) {
      setMessage(errorText(error, t));
    }
  }

  return (
    <Screen>
      <Message text={message} />
      {!complete.length && !missing_one.length ? (
        <Text style={styles.body}>{t("cook.none")}</Text>
      ) : null}
      {complete.length ? (
        <>
          <SectionTitle text={t("cook.complete")} />
          <View style={styles.list}>
            {complete.map((c) => (
              <RecipeCard key={c.recipe.id} recipe={c.recipe} />
            ))}
          </View>
        </>
      ) : null}
      {missing_one.length ? (
        <>
          <SectionTitle text={t("cook.missingOne")} />
          <View style={styles.list}>
            {missing_one.map((c) => {
              const lack = c.missing[0];
              return (
                <View key={c.recipe.id} style={styles.missing}>
                  <RecipeCard recipe={c.recipe} />
                  <Text style={styles.lack}>{t("cook.missing", { name: lack.name })}</Text>
                  {added.has(lack.ingredient_id) ? (
                    <Text style={styles.done}>{t("cook.added", { name: lack.name })}</Text>
                  ) : (
                    <BigButton
                      label={t("cook.addToList", { name: lack.name })}
                      icon="cart-outline"
                      variant="secondary"
                      onPress={() => addToList(lack.ingredient_id, lack.name)}
                    />
                  )}
                </View>
              );
            })}
          </View>
        </>
      ) : null}
      <Text style={styles.muted}>{t("cook.staples")}</Text>
    </Screen>
  );
}

export default function CookScreen() {
  return <SignedIn>{(auth) => <Cook auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  body: { fontSize: fontSize.body, color: colors.ink },
  list: { gap: spacing.m },
  missing: { gap: spacing.s },
  lack: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  done: { fontSize: fontSize.body, fontWeight: "600", color: colors.success },
  muted: { fontSize: fontSize.small, color: colors.muted, marginTop: spacing.m },
});
