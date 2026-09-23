/** Access screens. Someone already signed in goes straight to the home screen. */
import { Redirect, Stack } from "expo-router";

import { HomeLogo } from "../../components/HomeLogo.tsx";
import { colors } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { useSession } from "../../services/session.tsx";

export default function AuthLayout() {
  const { user } = useSession();
  const { t } = useI18n();
  if (user) return <Redirect href="/" />;
  return (
    <Stack
      screenOptions={{
        headerTintColor: colors.ink,
        headerBackTitle: t("common.back"),
        headerTitle: "",
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
        headerRight: () => <HomeLogo size={36} />,
      }}
    >
      <Stack.Screen name="login" options={{ headerShown: false }} />
    </Stack>
  );
}
