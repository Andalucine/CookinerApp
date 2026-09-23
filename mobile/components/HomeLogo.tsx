/** The anagram at the top of every screen: always a link to Inicio. */
import { router } from "expo-router";
import { Pressable } from "react-native";

import { useI18n } from "../i18n";
import { Logo } from "./Logo.tsx";

export function HomeLogo({ size = 40 }: { size?: number }) {
  const { t } = useI18n();
  function goHome() {
    if (router.canDismiss()) router.dismissTo("/");
    else router.replace("/");
  }
  return (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={t("common.goHome")}
      onPress={goHome}
      hitSlop={8}
    >
      <Logo small size={size} />
    </Pressable>
  );
}
