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
      <Stack.Screen name="wines/index" options={{ title: t("home.wines") }} />
      <Stack.Screen name="spices/index" options={{ title: t("home.spices") }} />
      <Stack.Screen name="notes/index" options={{ title: t("home.notes") }} />
      <Stack.Screen name="pantry/index" options={{ title: t("home.pantry") }} />
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
