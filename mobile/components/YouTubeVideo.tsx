/**
 * A YouTube video inside the recipe. YouTube asks embedded players to say which site they are
 * on, so the player is loaded from a small page with a base address; "Ver en YouTube" opens the
 * video outside the app if the player cannot show it.
 */
import * as WebBrowser from "expo-web-browser";
import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

import { useI18n } from "../i18n";
import { BigButton } from "./BigButton.tsx";
import { colors, radius, spacing } from "./theme.ts";

export function YouTubeVideo({ id, url }: { id: string; url: string }) {
  const { t } = useI18n();
  const html = `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0;height:100%;background:#000}iframe{border:0;width:100%;height:100%}</style></head>
<body><iframe src="https://www.youtube-nocookie.com/embed/${id}?playsinline=1&rel=0"
allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen"
referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></body></html>`;
  return (
    <View style={styles.wrapper}>
      <View style={styles.player}>
        <WebView
          source={{ html, baseUrl: "https://cookinerapp.com" }}
          allowsInlineMediaPlayback
          allowsFullscreenVideo
          mediaPlaybackRequiresUserAction
          scrollEnabled={false}
          style={styles.web}
        />
      </View>
      <BigButton
        label={t("recipe.openYoutube")}
        icon="logo-youtube"
        variant="link"
        onPress={() => WebBrowser.openBrowserAsync(url)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  player: {
    aspectRatio: 16 / 9,
    borderRadius: radius.m,
    overflow: "hidden",
    backgroundColor: colors.ink,
  },
  web: { flex: 1, backgroundColor: colors.ink },
});
