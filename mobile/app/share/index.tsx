/**
 * Compartir mi cuaderno (session 8): the people with access and their role (tap one to change
 * it or to remove the access), invite as viewer or editor with a code that is sent from the
 * phone's share menu, and the unused codes. On the free plan, an explanation instead.
 */
import { useState } from "react";
import { Alert, Pressable, Share, StyleSheet, Text, View } from "react-native";

import { BigButton } from "../../components/BigButton.tsx";
import { Chips } from "../../components/Chips.tsx";
import { LoadError, Loading } from "../../components/LoadState.tsx";
import { Message } from "../../components/Message.tsx";
import { Screen } from "../../components/Screen.tsx";
import { SectionTitle } from "../../components/SectionTitle.tsx";
import { type Auth, SignedIn } from "../../components/SignedIn.tsx";
import { colors, fontSize, radius, spacing } from "../../components/theme.ts";
import { useI18n } from "../../i18n";
import { errorText } from "../../services/errors.ts";
import * as notebooks from "../../services/notebooks.ts";
import { type Role, shortDate } from "../../services/sharedNotebook.ts";
import { useLoad } from "../../services/useLoad.ts";

function ShareNotebook({ auth }: { auth: Auth }) {
  const { t, language } = useI18n();
  const data = useLoad(async () => {
    const [mine, accesses, invitations] = await Promise.all([
      notebooks.mine(auth),
      notebooks.accesses(auth),
      notebooks.invitations(auth),
    ]);
    return { mine, accesses, invitations };
  }, [auth.token, auth.language]);
  const [open, setOpen] = useState<number | null>(null); // the person being changed
  const [created, setCreated] = useState<notebooks.Invitation | null>(null);
  const [busy, setBusy] = useState<string | null>(null); // which button is working
  const [message, setMessage] = useState<string | null>(null);

  if (data.loading && !data.data) return <Loading />;
  if (data.error || !data.data) {
    return (
      <Screen>
        <LoadError error={data.error} onRetry={data.reload} />
      </Screen>
    );
  }

  const { mine, accesses, invitations } = data.data;
  const roleName = (role: Role) => t(role === "editor" ? "role.editor" : "role.viewer");
  const max = mine.max_shared_with;

  if (max === 0) {
    return (
      <Screen>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{t("share.freeTitle")}</Text>
          <Text style={styles.body}>{t("share.freeText")}</Text>
        </View>
      </Screen>
    );
  }

  /** Run a change, show the API's message if it fails, and load the screen again. */
  async function act(key: string, action: () => Promise<unknown>) {
    setBusy(key);
    setMessage(null);
    try {
      await action();
      await data.reload();
    } catch (error) {
      setMessage(errorText(error, t));
    } finally {
      setBusy(null);
    }
  }

  function sendCode(code: string) {
    Share.share({ message: t("share.message", { code }) }).catch(() => {});
  }

  function confirmRemove(access: notebooks.Access) {
    Alert.alert(t("share.removeTitle"), t("share.removeText", { name: access.user.display_name }), [
      { text: t("common.cancel"), style: "cancel" },
      {
        text: t("share.remove"),
        style: "destructive",
        onPress: () =>
          act(`remove-${access.user.id}`, async () => {
            await notebooks.removeAccess(auth, access.user.id);
            setOpen(null);
          }),
      },
    ]);
  }

  function confirmCancel(invitation: notebooks.Invitation) {
    Alert.alert(t("share.cancelTitle"), t("share.cancelText", { code: invitation.code }), [
      { text: t("common.back"), style: "cancel" },
      {
        text: t("share.cancel"),
        style: "destructive",
        onPress: () =>
          act(`cancel-${invitation.id}`, async () => {
            await notebooks.cancelInvitation(auth, invitation.id);
            if (created?.id === invitation.id) setCreated(null);
          }),
      },
    ]);
  }

  function invite(role: Role) {
    act(`invite-${role}`, async () => setCreated(await notebooks.invite(auth, role)));
  }

  const limitReached = max !== null && accesses.length >= max;
  const others = invitations.filter((i) => i.id !== created?.id);

  return (
    <Screen>
      <Message text={message} />

      <SectionTitle
        text={
          max === null
            ? t("share.peopleNoLimit", { count: accesses.length })
            : t("share.people", { count: accesses.length, max })
        }
      />
      {accesses.length === 0 ? (
        <Text style={styles.muted}>{t("share.nobody")}</Text>
      ) : (
        <>
          <Text style={styles.muted}>{t("share.tapPerson")}</Text>
          <View style={styles.list}>
            {accesses.map((access) => {
              const isOpen = open === access.user.id;
              return (
                <View key={access.user.id} style={[styles.person, isOpen && styles.personOpen]}>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityState={{ expanded: isOpen }}
                    accessibilityLabel={`${access.user.display_name}, ${roleName(access.role)}`}
                    onPress={() => setOpen(isOpen ? null : access.user.id)}
                    style={({ pressed }) => [styles.personRow, pressed && styles.pressed]}
                  >
                    <Text style={styles.personName}>{access.user.display_name}</Text>
                    <Text style={styles.personRole}>{roleName(access.role)}</Text>
                  </Pressable>
                  {isOpen ? (
                    <View style={styles.personActions}>
                      <Chips
                        label={t("share.roleOf", { name: access.user.display_name })}
                        value={access.role}
                        onChange={(role) => {
                          if (role && role !== access.role) {
                            act(`role-${access.user.id}`, () =>
                              notebooks.changeRole(auth, access.user.id, role as Role),
                            );
                          }
                        }}
                        options={[
                          { value: "viewer", label: t("share.roleViewer") },
                          { value: "editor", label: t("share.roleEditor") },
                        ]}
                      />
                      <BigButton
                        label={t("share.remove")}
                        icon="person-remove-outline"
                        variant="secondary"
                        loading={busy === `remove-${access.user.id}`}
                        onPress={() => confirmRemove(access)}
                      />
                    </View>
                  ) : null}
                </View>
              );
            })}
          </View>
        </>
      )}

      <SectionTitle text={t("share.invite")} />
      {limitReached ? (
        <Text style={styles.body}>{t("share.limitReached", { max: max ?? 0 })}</Text>
      ) : (
        <>
          <Text style={styles.muted}>{t("share.roles")}</Text>
          <View style={styles.pair}>
            <View style={styles.half}>
              <BigButton
                label={t("share.inviteViewer")}
                icon="eye-outline"
                iconCircle
                layout="column"
                variant="secondary"
                fill
                loading={busy === "invite-viewer"}
                onPress={() => invite("viewer")}
              />
            </View>
            <View style={styles.half}>
              <BigButton
                label={t("share.inviteEditor")}
                icon="create-outline"
                iconCircle
                layout="column"
                variant="secondary"
                fill
                loading={busy === "invite-editor"}
                onPress={() => invite("editor")}
              />
            </View>
          </View>
        </>
      )}

      {created ? (
        <View style={styles.codeCard}>
          <Text style={styles.cardTitle}>
            {t("share.codeTitle", { role: roleName(created.role) })}
          </Text>
          <Text style={styles.code} selectable accessibilityLabel={created.code.split("").join(" ")}>
            {created.code}
          </Text>
          <Text style={styles.body}>
            {t("share.codeValid", { date: shortDate(created.expires_at, language) })}
          </Text>
          <BigButton
            label={t("share.send")}
            icon="share-outline"
            onPress={() => sendCode(created.code)}
          />
        </View>
      ) : null}

      {others.length ? (
        <>
          <SectionTitle text={t("share.pending")} />
          <View style={styles.list}>
            {others.map((invitation) => (
              <View key={invitation.id} style={styles.pending}>
                <Text style={styles.body} selectable>
                  {t("share.pendingItem", {
                    code: invitation.code,
                    role: roleName(invitation.role),
                    date: shortDate(invitation.expires_at, language),
                  })}
                </Text>
                <View style={styles.pair}>
                  <View style={styles.half}>
                    <BigButton
                      label={t("share.sendAgain")}
                      icon="share-outline"
                      variant="secondary"
                      onPress={() => sendCode(invitation.code)}
                    />
                  </View>
                  <View style={styles.half}>
                    <BigButton
                      label={t("share.cancel")}
                      icon="close-outline"
                      variant="secondary"
                      loading={busy === `cancel-${invitation.id}`}
                      onPress={() => confirmCancel(invitation)}
                    />
                  </View>
                </View>
              </View>
            ))}
          </View>
        </>
      ) : null}
    </Screen>
  );
}

export default function ShareScreen() {
  return <SignedIn>{(auth) => <ShareNotebook auth={auth} />}</SignedIn>;
}

const styles = StyleSheet.create({
  body: { fontSize: fontSize.body, color: colors.ink },
  muted: { fontSize: fontSize.body, color: colors.muted },
  list: { gap: spacing.s },
  // Two buttons of the same width side by side (rule of the app, session 7)
  pair: { flexDirection: "row", gap: spacing.s },
  half: { flex: 1 },
  card: {
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    backgroundColor: colors.surface,
  },
  cardTitle: { fontSize: fontSize.large, fontWeight: "800", color: colors.ink },
  person: { borderRadius: radius.m, borderWidth: 2, borderColor: colors.border },
  personOpen: { borderColor: colors.ink },
  personRow: {
    minHeight: 64,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.s,
    paddingHorizontal: spacing.m,
  },
  personName: { flex: 1, fontSize: fontSize.body, fontWeight: "700", color: colors.ink },
  personRole: { fontSize: fontSize.body, color: colors.muted },
  personActions: { gap: spacing.m, padding: spacing.m, paddingTop: 0 },
  pressed: { opacity: 0.7 },
  codeCard: {
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.accent,
    backgroundColor: colors.accentSoft,
  },
  code: {
    fontSize: 40,
    fontWeight: "800",
    letterSpacing: 6,
    color: colors.ink,
    textAlign: "center",
    paddingVertical: spacing.s,
  },
  pending: {
    gap: spacing.s,
    padding: spacing.m,
    borderRadius: radius.m,
    borderWidth: 2,
    borderColor: colors.border,
  },
});
