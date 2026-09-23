/** Language of the app: the account's language once signed in, the phone's before that. */
import { getLocales } from "expo-localization";
import { createContext, type ReactNode, useContext, useMemo, useState } from "react";

import { type Language, pickLanguage, type TextKey, translate } from "./translate.ts";

export type { Language, TextKey };

type I18n = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TextKey, params?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() =>
    pickLanguage(getLocales()[0]?.languageCode),
  );
  const value = useMemo<I18n>(
    () => ({ language, setLanguage, t: (key, params) => translate(language, key, params) }),
    [language],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside <I18nProvider>");
  return value;
}
