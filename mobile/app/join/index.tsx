/**
 * Unirme a un cuaderno (session 8): type the code someone sent → "Unirme" → the notebook opens
 * from "Abrir el cuaderno de NOMBRE" (and is kept in Mi cuenta → Cuadernos compartidos conmigo).
 */
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { TextField } from "../../components/TextField.tsx";
import { colors, fontSize } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as notebooks from "../../services/notebooks.ts";
import {
  CODE_LENGTH,
  isCompleteCode,
  normalizeCode,
  notebookParams,
} from "../../services/sharedNotebook.ts";

function Join({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [joined, setJoined] = useState<notebooks.SharedNotebook | null>(null);

  async function submit() {
    if (!isCompleteCode(code)) {
      setError(t("join.errorCode"));
      return;
    }
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      setJoined(await notebooks.join(auth, normalizeCode(code)));
    } catch (e) {
      setMessage(errorText(e, t));
    } finally {
      setBusy(false);
    }
  }

  if (joined) {
    const name = joined.owner.display_name;
    const role = t(joined.role === "editor" ? "role.editor" : "role.viewer");
    return (
      <Screen>
        <Message kind="ok" text={t("join.done", { name, role })} />
        <BigButton
          label={t("join.open", { name })}
          icon="book-outline"
          onPress={() =>
            router.replace({
              pathname: "/recipes",
              params: notebookParams({ id: joined.id, owner: name, role: joined.role }),
            })
          }
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <Text style={styles.body}>{t("join.intro")}</Text>
      <TextField
        label={t("join.code")}
        hint={t("join.codeHint")}
        value={code}
        onChangeText={setCode}
        error={error}
        autoCapitalize="characters"
        autoCorrect={false}
        autoComplete="off"
        maxLength={CODE_LENGTH + 4} // room for a space or a dash typed in the middle
        returnKeyType="go"
        onSubmitEditing={submit}
        style={styles.code}
      />
      <Message text={message} />
      <BigButton label={t("join.submit")} icon="enter-outline" loading={busy} onPress={submit} />
    </Screen>
  );
}

export default function JoinScreen() {
  return <SignedIn>{(auth) => <Join auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  body: { fontSize: fontSize.body, color: colors.ink },
  code: { fontSize: 26, fontWeight: "700", letterSpacing: 4 },
});
