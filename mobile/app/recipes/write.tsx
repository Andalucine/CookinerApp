/**
 * Escribir a mano (new recipe) and Editar (with ?id=). Saving a new recipe opens it; saving
 * an edit goes back to it. Borrar only for the notebook owner or whoever wrote the recipe.
 * A new recipe goes to someone else's notebook when it arrives with its parameters (editors).
 */
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Alert, StyleSheet, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { NotebookBanner } from "../../components/NotebookBanner.tsx";
import { emptyRecipe, RecipeForm } from "../../components/RecipeForm.tsx";
import { Screen } from "../../components/Screen.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as recipes from "../../services/recipes.ts";
import { type OtherNotebook, readNotebook } from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

/** The saved recipe → what the form edits. */
function toInput(recipe: recipes.Recipe): recipes.RecipeInput {
  return {
    title: recipe.title,
    description: recipe.description,
    instructions: recipe.instructions,
    prep_time_minutes: recipe.prep_time_minutes,
    servings: recipe.servings,
    cook_name: recipe.cook_name,
    source_type: recipe.source_type,
    source_name: recipe.source_name,
    source_url: recipe.source_url,
    youtube_url: recipe.youtube_url,
    image_url: recipe.image_url,
    language: recipe.language,
    ingredients: recipe.ingredients.map(({ name, quantity, unit, raw_text }) => ({
      name,
      quantity,
      unit,
      raw_text,
    })),
    category_ids: [
      ...recipe.categories.filter((c) => c.is_primary),
      ...recipe.categories.filter((c) => !c.is_primary),
    ].map((c) => c.id),
    tag_ids: recipe.tags.map((x) => x.id),
    season_ids: recipe.seasons.map((x) => x.id),
    occasion_ids: recipe.occasions.map((x) => x.id),
  };
}

function NewRecipe({ auth, notebook }: { auth: Auth; notebook: OtherNotebook | null }) {
  const { t } = useI18n();
  return (
    <Screen>
      <NotebookBanner notebook={notebook} />
      <RecipeForm
        auth={auth}
        initial={emptyRecipe(auth.language)}
        notebookId={notebook?.id}
        submitLabel={t("form.save")}
        onSubmit={async (input) => {
          const saved = await recipes.create(
            auth,
            notebook ? { ...input, notebook_id: notebook.id } : input,
          );
          router.replace(`/recipes/${saved.id}`);
        }}
      />
    </Screen>
  );
}

function EditRecipe({ auth, id }: { auth: Auth; id: number }) {
  const { t } = useI18n();
  const data = useLoad(() => recipes.get(auth, id), [auth.token, auth.language, id]);
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
  const recipe = data.data;
  const canDelete = recipe.my_role === "owner" || recipe.author?.id === auth.user.id;

  function confirmDelete() {
    Alert.alert(t("form.deleteTitle"), t("form.deleteText", { title: recipe.title }), [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("form.delete"), style: "destructive", onPress: remove },
    ]);
  }

  async function remove() {
    setDeleting(true);
    setMessage(null);
    try {
      await recipes.remove(auth, recipe.id);
      router.dismissTo("/recipes");
    } catch (error) {
      setMessage(errorText(error, t));
      setDeleting(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: t("recipe.edit") }} />
      {/* key: a fresh form when the recipe is loaded again */}
      <RecipeForm
        key={recipe.updated_at}
        auth={auth}
        initial={toInput(recipe)}
        notebookId={recipe.notebook_id}
        submitLabel={t("form.saveChanges")}
        onSubmit={async (input) => {
          await recipes.update(auth, recipe.id, input);
          router.back();
        }}
      />
      {canDelete ? (
        <View style={styles.danger}>
          <Message text={message} />
          <BigButton
            label={t("form.delete")}
            icon="trash-outline"
            variant="secondary"
            loading={deleting}
            onPress={confirmDelete}
          />
        </View>
      ) : null}
    </Screen>
  );
}

export default function WriteScreen() {
  const params = useLocalSearchParams<{ id?: string }>();
  const notebook = readNotebook(params);
  return (
    <SignedIn>
      {(auth) =>
        params.id ? (
          <EditRecipe auth={auth} id={Number(params.id)} />
        ) : (
          <NewRecipe auth={auth} notebook={notebook} />
        )
      }
    </SignedIn>
  );
}

const styles = StyleSheet.create({ danger: { marginTop: spacing.xl, gap: spacing.s } });
