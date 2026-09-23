/**
 * Inicio: the five doors (Recetas · Vinos · Especias · Notas · Mi despensa), the shopping list
 * always at hand and, further down, Compartir mi cuaderno with Unirme a un cuaderno and Mi cuenta
 * side by side (layout decided in session 6). Without a session it sends the person to Entrar.
 */
import { Ionicons } from "@expo/vector-icons";
import { type Href, Redirect, router } from "expo-router";
import type { ComponentProps } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../components/BigButton.tsx";
import { HomeLogo } from "../components/HomeLogo.tsx";
import { Logo } from "../components/Logo.tsx";
import { Screen } from "../components/Screen.tsx";
import { colors, fontSize, radius, spacing } from "../components/theme.ts";
import { type TextKey, useI18n } from "../i18n";
import { useSession } from "../services/session.tsx";

type IconName = ComponentProps<typeof Ionicons>["name"];

const DOORS: { label: TextKey; icon: IconName; href: Href }[] = [
  { label: "home.recipes", icon: "book-outline", href: "/recipes" },
  { label: "home.wines", icon: "wine-outline", href: "/wines" },
  { label: "home.spices", icon: "leaf-outline", href: "/spices" },
  { label: "home.notes", icon: "document-text-outline", href: "/notes" },
  { label: "home.pantry", icon: "basket-outline", href: "/pantry" },
];

export default function Home() {
  const { t } = useI18n();
  const { ready, user } = useSession();

  if (!ready) {
    return (
      <View style={styles.loading}>
        <Logo size={160} />
        <ActivityIndicator size="large" color={colors.ink} accessibilityLabel={t("common.loading")} />
      </View>
    );
  }
  if (!user) return <Redirect href="/login" />;

  return (
    <Screen>
      <View style={styles.header}>
        <HomeLogo size={56} />
        <View style={styles.headerText}>
          <Text style={styles.greeting} numberOfLines={1}>
            {t("home.greeting", { name: user.display_name })}
          </Text>
          {/* This line stays empty on purpose (session 6): the notebook name is not shown here */}
          <Text style={styles.subtitle}> </Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {t("home.plan", { plan: t(`plan.${user.plan}` as TextKey) })}
          </Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("home.shoppingList")}
          onPress={() => router.push("/shopping-list")}
          style={({ pressed }) => [styles.cart, pressed && styles.pressed]}
        >
          <Ionicons name="cart-outline" size={30} color={colors.ink} />
        </Pressable>
      </View>

      <View style={styles.grid}>
        {DOORS.map((door, index) => (
          <Pressable
            key={door.label}
            accessibilityRole="button"
            accessibilityLabel={t(door.label)}
            onPress={() => router.push(door.href)}
            style={({ pressed }) => [
              styles.door,
              index === DOORS.length - 1 && styles.doorWide,
              pressed && styles.pressed,
            ]}
          >
            <View style={styles.doorIcon}>
              <Ionicons name={door.icon} size={34} color={colors.ink} />
            </View>
            <Text style={styles.doorLabel}>{t(door.label)}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.links}>
        <BigButton
          label={t("home.share")}
          icon="people-outline"
          iconCircle
          variant="secondary"
          onPress={() => router.push("/share")}
        />
        {/* Two buttons of the same size side by side: circle above, text below */}
        <View style={styles.row}>
          <View style={styles.half}>
            <BigButton
              label={t("home.join")}
              icon="enter-outline"
              iconCircle
              layout="column"
              fill
              variant="secondary"
              onPress={() => router.push("/join")}
            />
          </View>
          <View style={styles.half}>
            <BigButton
              label={t("home.settings")}
              icon="person-circle-outline"
              iconCircle
              layout="column"
              fill
              variant="secondary"
              onPress={() => router.push("/settings")}
            />
          </View>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.l,
    backgroundColor: colors.background,
  },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.m },
  headerText: { flex: 1 },
  greeting: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  subtitle: { fontSize: fontSize.small, color: colors.muted },
  cart: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: colors.ink,
    alignItems: "center",
    justifyContent: "center",
  },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.m, marginTop: spacing.s },
  door: {
    flexBasis: "47%",
    flexGrow: 1,
    minHeight: 132,
    borderRadius: radius.l,
    borderWidth: 2,
    borderColor: colors.ink,
    backgroundColor: colors.background,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.s,
    padding: spacing.m,
  },
  doorWide: { flexBasis: "100%", minHeight: 104, flexDirection: "row", gap: spacing.m },
  doorIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  doorLabel: { fontSize: fontSize.large, fontWeight: "700", color: colors.ink, textAlign: "center" },
  pressed: { opacity: 0.7 },
  // Twice the previous distance from Mi despensa (session 6): 16 + 48 = 64
  links: { gap: spacing.m, marginTop: spacing.xl + spacing.m },
  row: { flexDirection: "row", gap: spacing.m, alignItems: "stretch" },
  half: { flex: 1, flexDirection: "column" },
});
