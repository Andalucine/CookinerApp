/** A photo kept by the API (session 9): a thumbnail that opens full screen when tapped, and
 * the button to add, change or remove it (camera or gallery). */
import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import { useState } from "react";
import { Alert, Image, Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "../i18n";
import { errorText } from "../services/errors.ts";
import * as photos from "../services/photos.ts";
import { BigButton } from "./BigButton.tsx";
import { colors, fontSize, radius, spacing } from "./theme.ts";

type Auth = { token: string; language: string };

/** The thumbnail. `size` in points; tapping it shows the photo full screen. */
export function PhotoThumb({
  url,
  size = 56,
  label,
}: {
  url: string | null | undefined;
  size?: number;
  label?: string;
}) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const uri = photos.photoUri(url);
  if (!uri) return null;
  return (
    <>
      <Pressable
        accessibilityRole="imagebutton"
        accessibilityLabel={label ?? t("photo.see")}
        onPress={() => setOpen(true)}
        hitSlop={6}
      >
        <Image
          source={{ uri }}
          style={{ width: size, height: size, borderRadius: Math.round(size / 5) }}
          accessibilityIgnoresInvertColors
        />
      </Pressable>
      <PhotoViewer uri={open ? uri : null} onClose={() => setOpen(false)} />
    </>
  );
}

export function PhotoViewer({ uri, onClose }: { uri: string | null; onClose: () => void }) {
  const { t } = useI18n();
  return (
    <Modal visible={!!uri} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel={t("photo.close")}>
        {uri ? (
          <Image source={{ uri }} style={styles.full} resizeMode="contain" />
        ) : null}
        <View style={styles.closeRow}>
          <Ionicons name="close" size={28} color={colors.background} />
          <Text style={styles.closeText}>{t("photo.close")}</Text>
        </View>
      </Pressable>
    </Modal>
  );
}

/** Take a photo or pick one from the gallery, send it to the API and return its address. */
export async function pickPhoto(auth: Auth, from: "camera" | "gallery"): Promise<string | null> {
  const options: ImagePicker.ImagePickerOptions = {
    mediaTypes: ["images"],
    allowsEditing: true,
    quality: 0.7, // plenty for a phone screen, and light to send
  };
  if (from === "camera") {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) throw new Error("no-camera");
  } else {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) throw new Error("no-gallery");
  }
  const result =
    from === "camera"
      ? await ImagePicker.launchCameraAsync(options)
      : await ImagePicker.launchImageLibraryAsync(options);
  if (result.canceled || !result.assets.length) return null;
  const asset = result.assets[0];
  const saved = await photos.upload(auth, asset.uri, asset.mimeType);
  return saved.url;
}

/** "Añadir foto" / "Cambiar foto" + "Quitar foto": asks camera or gallery, sends the photo and
 * tells the owner the new address (null when removed). */
export function PhotoButton({
  auth,
  url,
  onChange,
  compact = false,
}: {
  auth: Auth;
  url: string | null;
  onChange: (url: string | null) => void | Promise<void>;
  compact?: boolean; // the "link" look, for inside a list
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function pick(from: "camera" | "gallery") {
    setBusy(true);
    setMessage(null);
    try {
      const saved = await pickPhoto(auth, from);
      if (saved) await onChange(saved);
    } catch (error) {
      const reason = error instanceof Error ? error.message : "";
      setMessage(
        reason === "no-camera"
          ? t("photo.noCamera")
          : reason === "no-gallery"
            ? t("photo.noGallery")
            : errorText(error, t),
      );
    } finally {
      setBusy(false);
    }
  }

  function ask() {
    Alert.alert(url ? t("photo.change") : t("photo.add"), undefined, [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("photo.gallery"), onPress: () => pick("gallery") },
      { text: t("photo.camera"), onPress: () => pick("camera") },
    ]);
  }

  return (
    <View style={styles.buttons}>
      <BigButton
        label={url ? t("photo.change") : t("photo.add")}
        icon="camera-outline"
        variant={compact ? "link" : "secondary"}
        loading={busy}
        onPress={ask}
      />
      {url ? (
        <BigButton
          label={t("photo.remove")}
          icon="trash-outline"
          variant="link"
          onPress={() => onChange(null)}
        />
      ) : null}
      {message ? <Text style={styles.error}>{message}</Text> : null}
    </View>
  );
}

/** The photo of a form (recipe, wine): the picture above the button, session 9. */
export function PhotoField({
  auth,
  label,
  url,
  onChange,
}: {
  auth: Auth;
  label: string;
  url: string | null;
  onChange: (url: string | null) => void;
}) {
  const uri = photos.photoUri(url);
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      {uri ? (
        <Image source={{ uri }} style={styles.preview} accessibilityIgnoresInvertColors />
      ) : null}
      <PhotoButton auth={auth} url={url} onChange={onChange} />
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.92)",
    alignItems: "center",
    justifyContent: "center",
  },
  full: { width: "100%", height: "80%" },
  closeRow: {
    position: "absolute",
    top: 56,
    right: spacing.l,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  closeText: { color: colors.background, fontSize: fontSize.body, fontWeight: "600" },
  buttons: { gap: spacing.xs },
  error: { fontSize: fontSize.small, color: colors.error, fontWeight: "600" },
  field: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.ink },
  preview: {
    width: "100%",
    aspectRatio: 4 / 3,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
});
