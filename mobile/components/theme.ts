/**
 * Visual identity (session 3): black stroke and a single orange element.
 * Colours taken from the final logo files. Sizes are generous on purpose: the app is for people
 * with basic digital skills, so big text and big touch targets.
 */
export const colors = {
  ink: "#090909", // the black of the logo
  accent: "#FFBE00", // the orange of the logo
  accentSoft: "#FFF4D1",
  background: "#FFFFFF",
  surface: "#F6F5F2",
  border: "#D9D7D2",
  muted: "#5C5A55",
  error: "#B3261E",
  success: "#1E7B34",
};

export const spacing = { xs: 4, s: 8, m: 16, l: 24, xl: 32 };

export const fontSize = { small: 16, body: 18, large: 22, title: 28 };

export const radius = { m: 14, l: 20 };

/** Minimum height of anything you touch (Apple asks for 44; we go bigger). */
export const touchHeight = 56;
