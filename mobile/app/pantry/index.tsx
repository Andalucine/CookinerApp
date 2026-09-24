/**
 * Mi despensa (session 9): "¿Qué puedo cocinar?" in orange, then three blocks, Nevera,
 * Congelador and Despensa, each with what is noted (a tag with an X to remove it) and its own
 * field to add more. Tapping the name opens the photo options (session 9): add, change or
 * remove a photo of the product; its thumbnail sits in the tag and opens full screen. No
 * expiry dates (decision, session 3). Always my own notebook.
 */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import type { ComponentProps } from "react";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { AddField } from "../../components/AddField.tsx";
import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { RowButton } from "../../components/RowButton.tsx";
import { PhotoButton, PhotoThumb } from "../../components/Photo.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { IconCircle } from "../../components/SpiceIcons.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { type TextKey, useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { byLocation, LOCATIONS, pantryName } from "../../services/kitchen.ts";
import * as pantry from "../../services/pantry.ts";
import { useLoad } from "../../services/useLoad.ts";

type IconName = ComponentProps<typeof Ionicons>["name"];

const PLACE_ICONS: Record<pantry.Location, IconName> = {
  fridge: "thermometer-outline",
  freezer: "snow-outline",
  pantry: "file-tray-stacked-outline",
};

function Pantry({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const data = useLoad(() => pantry.get(auth), [auth.token, auth.language]);
  const [message, setMessage] = useState<string | null>(null);
  const [photoFor, setPhotoFor] = useState<number | null>(null); // the item with photo options open

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const items = data.data.items;
  const groups = byLocation(items);

  async function add(place: pantry.Location, text: string) {
    const name = pantryName(text);
    if (!name) return;
    setMessage(null);
    try {
      const item = await pantry.add(auth, name, place);
      // the same ingredient in another place moves: the API keeps one of each
      const rest = items.filter((i) => i.ingredient_id !== item.ingredient_id);
      data.setData({ items: [...rest, item] });
    } catch (error) {
      setMessage(errorText(error, t));
      throw error;
    }
  }

  async function setPhoto(item: pantry.PantryItem, url: string | null) {
    setMessage(null);
    try {
      const saved = await pantry.setPhoto(auth, item.id, url);
      data.setData({ items: items.map((i) => (i.id === item.id ? saved : i)) });
      setPhotoFor(null);
    } catch (error) {
      setMessage(errorText(error, t));
    }
  }

  async function remove(item: pantry.PantryItem) {
    setMessage(null);
    data.setData({ items: items.filter((i) => i.id !== item.id) });
    try {
      await pantry.remove(auth, item.id);
    } catch (error) {
      setMessage(errorText(error, t));
      data.reload();
    }
  }

  return (
    <Screen>
      <Text style={styles.intro}>{t("pantry.intro")}</Text>
      <BigButton
        label={t("pantry.cook")}
        icon="restaurant-outline"
        onPress={() => router.push("/pantry/cook")}
      />
      <RowButton
        label={t("menu.title")}
        icon="calendar-outline"
        onPress={() => router.push("/menu")}
      />
      <Message text={message} />
      {LOCATIONS.map((place, index) => (
        <View key={place} style={styles.block}>
          <View style={styles.head}>
            <IconCircle name={PLACE_ICONS[place]} size={40} />
            <Text style={styles.title} accessibilityRole="header">
              {t(`pantry.place.${place}` as TextKey)}
            </Text>
            <Text style={styles.count}>{groups[place].length}</Text>
          </View>
          {groups[place].length ? (
            <View style={styles.tags}>
              {groups[place].map((item) => (
                <View key={item.id} style={styles.tagWrap}>
                  <View style={[styles.tag, photoFor === item.id && styles.tagOpen]}>
                    <PhotoThumb url={item.image_url} size={36} label={item.name} />
                    <Pressable
                      accessibilityRole="button"
                      accessibilityLabel={t("photo.options", { name: item.name })}
                      onPress={() => setPhotoFor(photoFor === item.id ? null : item.id)}
                      style={({ pressed }) => [styles.tagName, pressed && styles.pressed]}
                    >
                      <Text style={styles.tagText}>{item.name}</Text>
                    </Pressable>
                    <Pressable
                      accessibilityRole="button"
                      accessibilityLabel={t("pantry.remove", { name: item.name })}
                      onPress={() => remove(item)}
                      hitSlop={8}
                      style={({ pressed }) => [styles.tagClose, pressed && styles.pressed]}
                    >
                      <Ionicons name="close" size={20} color={colors.ink} />
                    </Pressable>
                  </View>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.muted}>{t("pantry.blockEmpty")}</Text>
          )}
          {groups[place].some((i) => i.id === photoFor) ? (
            <View style={styles.photoOptions}>
              <Text style={styles.photoTitle}>
                {t("photo.options", {
                  name: groups[place].find((i) => i.id === photoFor)!.name,
                })}
              </Text>
              <PhotoButton
                auth={auth}
                url={groups[place].find((i) => i.id === photoFor)!.image_url}
                onChange={(url) => setPhoto(groups[place].find((i) => i.id === photoFor)!, url)}
                compact
              />
            </View>
          ) : null}
          <AddField
            label={t(`pantry.addTo.${place}` as TextKey)}
            hint={index === 0 ? t("pantry.addHint") : undefined}
            onAdd={(text) => add(place, text)}
          />
        </View>
      ))}
    </Screen>
  );
}

export default function PantryScreen() {
  return <SignedIn>{(auth) => <Pantry auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  intro: { fontSize: fontSize.body, color: colors.ink },
  block: {
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
  head: { flexDirection: "row", alignItems: "center", gap: spacing.s },
  title: { flex: 1, fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  count: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  tags: { flexDirection: "row", flexWrap: "wrap", gap: spacing.s },
  tagWrap: {},
  tag: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    minHeight: 44,
    paddingLeft: spacing.xs,
    paddingRight: spacing.s,
    borderRadius: 22,
    backgroundColor: colors.accentSoft,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  tagOpen: { borderColor: colors.ink },
  tagName: { minHeight: 40, justifyContent: "center", paddingHorizontal: spacing.xs },
  tagClose: { minHeight: 40, justifyContent: "center", paddingLeft: spacing.xs },
  tagText: { fontSize: fontSize.body, color: colors.ink },
  photoOptions: {
    gap: spacing.xs,
    padding: spacing.s,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  photoTitle: { fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  pressed: { opacity: 0.7 },
  muted: { fontSize: fontSize.body, color: colors.muted },
});
