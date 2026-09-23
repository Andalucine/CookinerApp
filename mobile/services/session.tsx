/**
 * The signed-in person. The token is kept in the phone's secure storage (Keychain on iPhone),
 * so the app does not ask to sign in every day (the token lasts 30 days).
 */
import * as SecureStore from "expo-secure-store";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { useI18n } from "../i18n";
import { ApiError } from "./apiClient.ts";
import * as auth from "./auth.ts";

const TOKEN_KEY = "cookinerapp.token";

type Session = {
  ready: boolean; // false while reading the saved token at start-up
  token: string | null;
  user: auth.User | null;
  signIn: (token: string, user: auth.User) => Promise<void>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const { language, setLanguage } = useI18n();
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<auth.User | null>(null);

  const signIn = useCallback(
    async (newToken: string, newUser: auth.User) => {
      await SecureStore.setItemAsync(TOKEN_KEY, newToken);
      setToken(newToken);
      setUser(newUser);
      setLanguage(newUser.language);
    },
    [setLanguage],
  );

  const signOut = useCallback(async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // At start-up: if there is a saved token and it still works, go straight in.
  useEffect(() => {
    (async () => {
      const saved = await SecureStore.getItemAsync(TOKEN_KEY);
      if (saved) {
        try {
          const current = await auth.me(saved, language);
          setToken(saved);
          setUser(current);
          setLanguage(current.language);
        } catch (error) {
          // An expired or invalid token is forgotten; a network problem keeps it for next time
          if (error instanceof ApiError && error.status === 401) {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
          }
        }
      }
      setReady(true);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SessionContext.Provider value={{ ready, token, user, signIn, signOut }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): Session {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside <SessionProvider>");
  return value;
}
