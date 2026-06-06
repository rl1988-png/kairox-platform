'use client';

import { createContext, useContext, useMemo, useState } from 'react';
import de from '../../../messages/de.json';
import en from '../../../messages/en.json';

type Locale = 'de' | 'en';
type Messages = typeof de;

const catalogs: Record<Locale, Messages> = { de, en };

const I18nContext = createContext<{ locale: Locale; t: (key: string) => string }>({
  locale: 'de',
  t: (key) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale] = useState<Locale>('de');
  const value = useMemo(() => {
    const catalog = catalogs[locale];
    const t = (key: string): string => {
      const parts = key.split('.');
      let cur: unknown = catalog;
      for (const p of parts) {
        if (cur && typeof cur === 'object' && p in cur) {
          cur = (cur as Record<string, unknown>)[p];
        } else {
          return key;
        }
      }
      return typeof cur === 'string' ? cur : key;
    };
    return { locale, t };
  }, [locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useTranslations() {
  return useContext(I18nContext);
}
