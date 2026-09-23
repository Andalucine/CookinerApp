/** The CookinerApp logo (full) or the anagram (small, for headers). */
import { Image, StyleSheet } from "react-native";

export function Logo({ size = 180, small = false }: { size?: number; small?: boolean }) {
  return (
    <Image
      source={small ? require("../assets/anagram.png") : require("../assets/logo.png")}
      style={[styles.image, { width: size, height: size }]}
      accessibilityLabel="CookinerApp"
      resizeMode="contain"
    />
  );
}

const styles = StyleSheet.create({ image: { alignSelf: "center" } });
