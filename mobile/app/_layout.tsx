/** Root of the app: language, session and the navigation stack with the screen titles. */
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { HomeLogo } from "../components/HomeLogo.tsx";
import { colors } from "../components/theme.ts";
import { I18nProvider, useI18n } from "../i18n";
import { SessionProvider } from "../services/session.tsx";

function Navigation() {
  const { t } = useI18n();
  return (
    <Stack
      screenOptions={{
        headerTintColor: colors.ink,
        headerStyle: { backgroundColor: colors.background },
        headerTitleStyle: { fontSize: 20, fontWeight: "700" },
        headerBackTitle: t("common.back"),
        contentStyle: { backgroundColor: colors.background },
        headerRight: () => <HomeLogo size={36} />,
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="recipes/index" options={{ title: t("home.recipes") }} />
      <Stack.Screen name="recipes/categories" options={{ title: t("categories.title") }} />
      <Stack.Screen name="recipes/search" options={{ title: t("recipes.search") }} />
      <Stack.Screen name="recipes/list" options={{ title: t("recipes.results") }} />
      <Stack.Screen name="recipes/[id]" options={{ title: t("recipes.recipe") }} />
      <Stack.Screen name="recipes/new" options={{ title: t("recipes.new") }} />
      <Stack.Screen name="recipes/write" options={{ title: t("new.write") }} />
      <Stack.Screen name="recipes/import" options={{ title: t("new.web") }} />
      <Stack.Screen name="wines/index" options={{ title: t("home.wines") }} />
      <Stack.Screen name="wines/categories" options={{ title: t("wines.byType") }} />
      <Stack.Screen name="wines/search" options={{ title: t("recipes.search") }} />
      <Stack.Screen name="wines/list" options={{ title: t("recipes.results") }} />
      <Stack.Screen name="wines/[id]" options={{ title: t("wines.wine") }} />
      <Stack.Screen name="wines/new" options={{ title: t("wines.new") }} />
      <Stack.Screen name="wines/write" options={{ title: t("new.write") }} />
      <Stack.Screen name="wines/import" options={{ title: t("new.web") }} />
      <Stack.Screen name="wines/recommend" options={{ title: t("recommend.title") }} />
      <Stack.Screen name="spices/index" options={{ title: t("home.spices") }} />
      <Stack.Screen name="spices/list" options={{ title: t("home.spices") }} />
      <Stack.Screen name="spices/rules" options={{ title: t("spices.rules") }} />
      <Stack.Screen name="spices/blend" options={{ title: t("blend.newTitle") }} />
      <Stack.Screen name="spices/spice" options={{ title: t("ownSpice.newTitle") }} />
      <Stack.Screen name="spices/substitutions" options={{ title: t("subs.title") }} />
      <Stack.Screen name="spices/[id]" options={{ title: t("home.spices") }} />
      <Stack.Screen name="notes/index" options={{ title: t("home.notes") }} />
      <Stack.Screen name="notes/[id]" options={{ title: t("notes.note") }} />
      <Stack.Screen name="notes/write" options={{ title: t("notes.new") }} />
      <Stack.Screen name="pantry/index" options={{ title: t("home.pantry") }} />
      <Stack.Screen name="pantry/cook" options={{ title: t("pantry.cook") }} />
      <Stack.Screen name="shopping-list/index" options={{ title: t("home.shoppingList") }} />
      <Stack.Screen name="share/index" options={{ title: t("home.share") }} />
      <Stack.Screen name="join/index" options={{ title: t("home.join") }} />
      <Stack.Screen name="settings/index" options={{ title: t("home.settings") }} />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <I18nProvider>
        <SessionProvider>
          <StatusBar style="dark" />
          <Navigation />
        </SessionProvider>
      </I18nProvider>
    </SafeAreaProvider>
  );
}
