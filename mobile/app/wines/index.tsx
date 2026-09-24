/**
 * Vinos (portada; session 9: the cellar is Vinoselección's, the same for every plan): Por tipos
 * and Buscar, how many wines the shop has for sale ("Ver todos"), and my favourites.
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
import { useI18n } from "../../i18n";
import { useLoad } from "../../services/useLoad.ts";
import * as wines from "../../services/wines.ts";

const FAVORITES = 5;

function WinesHome({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const data = useLoad(async () => {
    const [forSale, favorites] = await Promise.all([
      wines.search(auth, { in_stock: "true" }, 1),
      wines.search(auth, { favorites: "true" }, FAVORITES),
    ]);
    return { forSale: forSale.total, favorites };
  }, [auth.token, auth.language]);

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
      </View>

      {data.loading && !data.data ? (
        <Loading />
      ) : data.error || !data.data ? (
        <LoadError error={data.error} onRetry={data.reload} />
      ) : (
        <>
          <Text style={styles.intro}>{t("wines.shopIntro", { count: data.data.forSale })}</Text>
          {data.data.forSale > 0 ? (
            <RowButton
              label={t("wines.seeAll", { count: data.data.forSale })}
              strong
              onPress={() =>
                router.push({
                  pathname: "/wines/list",
                  params: { in_stock: "true", title: t("wines.all") },
                })
              }
            />
          ) : null}

          <SectionTitle text={t("wines.favorites")} />
          {data.data.favorites.total ? (
            <View style={styles.list}>
              {data.data.favorites.items.map((wine) => (
                <WineCard key={wine.id} wine={wine} />
              ))}
              {data.data.favorites.total > FAVORITES ? (
                <RowButton
                  label={t("wines.seeAll", { count: data.data.favorites.total })}
                  icon="star-outline"
                  onPress={() =>
                    router.push({
                      pathname: "/wines/list",
                      params: { favorites: "true", title: t("wines.favorites") },
                    })
                  }
                />
              ) : null}
            </View>
          ) : (
            <Text style={styles.muted}>{t("wines.favoritesNone")}</Text>
          )}
        </>
      )}
    </Screen>
  );
}

export default function WinesHomeScreen() {
  return <SignedIn>{(auth) => <WinesHome auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  buttons: { gap: spacing.m },
  list: { gap: spacing.s },
  intro: { fontSize: fontSize.body, color: colors.ink, lineHeight: 26 },
  muted: { fontSize: fontSize.body, color: colors.muted },
});
