/**
 * Vinos (portada, session 8): the three buttons (Por tipos · Buscar · Nuevo vino), the latest
 * wines of my notebook, "Ver todos" and "Mis favoritos". On the free plan, the explanation.
 */
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, spacing } from "../../components/theme.ts";
import { WineCard } from "../../components/WineCard.tsx";
import { winesAllowed, WinesNotInPlan } from "../../components/WinesGate.tsx";
import { useI18n } from "../../i18n";
import { useLoad } from "../../services/useLoad.ts";
import * as wines from "../../services/wines.ts";

const LATEST = 5;

function WinesHome({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const latest = useLoad(() => wines.search(auth, {}, LATEST), [auth.token, auth.language]);

  return (
    <Screen>
      <View style={styles.buttons}>
        <BigButton
          label={t("wines.byType")}
          icon="wine-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.push("/wines/categories")}
        />
        <BigButton
          label={t("recipes.search")}
          icon="search"
          iconCircle
          variant="secondary"
          onPress={() => router.push("/wines/search")}
        />
        <BigButton label={t("wines.new")} icon="add" onPress={() => router.push("/wines/new")} />
      </View>

      <SectionTitle text={t("wines.latest")} />
      {latest.loading && !latest.data ? (
        <Loading />
      ) : latest.error ? (
        <LoadError error={latest.error} onRetry={latest.reload} />
      ) : latest.data && latest.data.total > 0 ? (
        <View style={styles.list}>
          {latest.data.items.map((wine) => (
            <WineCard key={wine.id} wine={wine} />
          ))}
          {latest.data.total > LATEST ? (
            <RowButton
              label={t("wines.seeAll", { count: latest.data.total })}
              strong
              onPress={() =>
                router.push({ pathname: "/wines/list", params: { title: t("wines.all") } })
              }
            />
          ) : null}
          <RowButton
            label={t("wines.favorites")}
            icon="star-outline"
            onPress={() =>
              router.push({
                pathname: "/wines/list",
                params: { favorites: "true", title: t("wines.favorites") },
              })
            }
          />
        </View>
      ) : (
        <Text style={styles.empty}>{t("wines.empty")}</Text>
      )}
    </Screen>
  );
}

export default function WinesHomeScreen() {
  return (
    <SignedIn>
      {(auth) => (winesAllowed(auth.user) ? <WinesHome auth={auth} /> : <WinesNotInPlan />)}
    </SignedIn>
  );
}

const styles = StyleSheet.create({
  buttons: { gap: spacing.m },
  list: { gap: spacing.s },
  empty: { fontSize: fontSize.body, color: colors.muted },
});
