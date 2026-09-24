/** Weeks and days of the menu, without React Native (tested with Node), session 9. */
import type { Language } from "../i18n/translate.ts";
import type { Meal, Slot } from "./menu.ts";
import { shortDate } from "./sharedNotebook.ts";

export const MEALS: Meal[] = ["breakfast", "lunch", "dinner"];

/** "2026-09-30" (a Wednesday) → "2026-09-28" (its Monday). Dates as the phone sees them. */
export function mondayOf(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const shift = (date.getDay() + 6) % 7; // Sunday (0) is six days after Monday
  date.setDate(date.getDate() - shift);
  return toIso(date);
}

export function toIso(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function today(): string {
  return toIso(new Date());
}

/** The Monday `weeks` weeks after (or before, negative) the given Monday. */
export function shiftWeek(monday: string, weeks: number): string {
  const [y, m, d] = monday.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  date.setDate(date.getDate() + 7 * weeks);
  return toIso(date);
}

/** The day `day` (0 = Monday) of that week, as "2026-09-30". */
export function dayOf(monday: string, day: number): string {
  const [y, m, d] = monday.split("-").map(Number);
  const date = new Date(y, m - 1, d + day);
  return toIso(date);
}

/** "del 28 de septiembre al 4 de octubre" / "28 September to 4 October" (and fr, nl, de). */
export function weekLabel(monday: string, language: Language): string {
  const from = shortDate(`${monday}T12:00:00`, language);
  const to = shortDate(`${dayOf(monday, 6)}T12:00:00`, language);
  const shapes: Record<Language, string> = {
    es: `del ${from} al ${to}`,
    en: `${from} to ${to}`,
    fr: `du ${from} au ${to}`,
    nl: `${from} tot ${to}`,
    de: `${from} bis ${to}`,
  };
  return shapes[language];
}

const DAY_NAMES: Record<Language, string[]> = {
  es: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
  en: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  fr: ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
  nl: ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"],
  de: ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
};

export function dayName(day: number, language: Language): string {
  return DAY_NAMES[language][day] ?? "";
}

/** Is that week the one we are in? */
export function isThisWeek(monday: string, now = today()): boolean {
  return mondayOf(now) === monday;
}

/** The slots of a day, in meal order. */
export function slotsOfDay(slots: Slot[], day: number): Slot[] {
  return slots
    .filter((s) => s.day === day)
    .sort((a, b) => MEALS.indexOf(a.meal) - MEALS.indexOf(b.meal));
}

/** The menu after one slot changed, before reloading. */
export function withSlot(slots: Slot[], changed: Slot): Slot[] {
  return slots.map((s) => (s.id === changed.id ? changed : s));
}
