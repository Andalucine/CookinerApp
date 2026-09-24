/** Escribir a mano (new wine) and Editar (with ?id=). Borrar only for the notebook owner or
 * whoever added the wine. */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, StyleSheet, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { spacing } from "../../components/theme.ts";
import { emptyWine, WineForm } from "../../components/WineForm.tsx";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import { useLoad } from "../../services/useLoad.ts";
import * as wines from "../../services/wines.ts";

function toInput(wine: wines.Wine): wines.WineInput {
  return {
    name: wine.name,
    winery: wine.winery,
    category_id: wine.category?.id ?? null,
    sweetness: wine.sweetness,
    body: wine.body,
    ageing: wine.ageing,
    country: wine.country,
    appellation: wine.appellation,
    grapes: wine.grapes,
    vintage: wine.vintage,
    price_range: wine.price_range,
    tasting_notes: wine.tasting_notes,
    pairing_notes: wine.pairing_notes,
    source_url: wine.source_url,
    source_name: wine.source_name,
    source_price: wine.source_price,
    image_url: wine.image_url,
  };
}

function NewWine({ auth }: { auth: Auth }) {
  const { t } = useI18n();
  return (
    <Screen>
      <WineForm
        auth={auth}
        initial={emptyWine()}
        submitLabel={t("wineForm.save")}
        onSubmit={async (input) => {
          const saved = await wines.create(auth, input);
          router.replace(`/wines/${saved.id}`);
        }}
      />
    </Screen>
  );
}

function EditWine({ auth, id }: { auth: Auth; id: number }) {
  const { t } = useI18n();
  const data = useLoad(() => wines.get(auth, id), [auth.token, auth.language, id]);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }
  const wine = data.data;

  function confirmDelete() {
    Alert.alert(t("wineForm.deleteTitle"), t("wineForm.deleteText", { name: wine.name }), [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("wineForm.delete"), style: "destructive", onPress: remove },
    ]);
  }

  async function remove() {
    setDeleting(true);
    setMessage(null);
    try {
      await wines.remove(auth, wine.id);
      router.dismissTo("/wines");
    } catch (error) {
      setMessage(errorText(error, t));
      setDeleting(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("recipe.edit") }} />
      <WineForm
        key={wine.updated_at}
        auth={auth}
        initial={toInput(wine)}
        submitLabel={t("form.saveChanges")}
        onSubmit={async (input) => {
          await wines.update(auth, wine.id, input);
          router.back();
        }}
      />
      <View style={styles.danger}>
        <Message text={message} />
        <BigButton
          label={t("wineForm.delete")}
          icon="trash-outline"
          variant="secondary"
          loading={deleting}
          onPress={confirmDelete}
        />
      </View>
    </Screen>
  );
}

export default function WineWriteScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  return (
    <SignedIn>
      {(auth) => (id ? <EditWine auth={auth} id={Number(id)} /> : <NewWine auth={auth} />)}
    </SignedIn>
  );
}

const styles = StyleSheet.create({ danger: { marginTop: spacing.xl, gap: spacing.s } });
