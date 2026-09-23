/** Screens of the notebook need a session: without one they go to Entrar. */
import { Redirect } from "expo-router";
import type { ReactNode } from "react";

import { type Language, useI18n } from "../i18n";
import type { User } from "../services/auth.ts";
import { useSession } from "../services/session.tsx";
import { Loading } from "./LoadState.tsx";

export type Auth = { token: string; user: User; language: Language };

export function SignedIn({ children }: { children: (auth: Auth) => ReactNode }) {
  const { ready, token, user } = useSession();
  const { language } = useI18n();
  if (!ready) return <Loading />;
  if (!token || !user) return <Redirect href="/login" />;
  return <>{children({ token, user, language })}</>;
}
