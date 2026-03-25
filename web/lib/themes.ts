export interface ThemeColors {
  name: string;
  slug: string;
  primary: string;
  secondary: string;
  accent: string;
  bg: string;
  surface: string;
  text: string;
  muted: string;
}

export const themes: Record<string, ThemeColors> = {
  aurora: {
    name: "Aurora",
    slug: "aurora",
    primary: "#F4A261",
    secondary: "#B48EAD",
    accent: "#81A1C1",
    bg: "#1a1a2e",
    surface: "#2E3440",
    text: "#ECEFF4",
    muted: "#4C566A",
  },
  midnight: {
    name: "Midnight",
    slug: "midnight",
    primary: "#7C3AED",
    secondary: "#06B6D4",
    accent: "#F43F5E",
    bg: "#0F172A",
    surface: "#1E293B",
    text: "#F8FAFC",
    muted: "#475569",
  },
  forest: {
    name: "Forest",
    slug: "forest",
    primary: "#4ADE80",
    secondary: "#A78BFA",
    accent: "#FCD34D",
    bg: "#1A2E1A",
    surface: "#2D4A2D",
    text: "#E8F5E8",
    muted: "#3D5A3D",
  },
  ocean: {
    name: "Ocean",
    slug: "ocean",
    primary: "#22D3EE",
    secondary: "#818CF8",
    accent: "#FB923C",
    bg: "#0C1222",
    surface: "#1E293B",
    text: "#E0F2FE",
    muted: "#1E3A5F",
  },
  monochrome: {
    name: "Monochrome",
    slug: "monochrome",
    primary: "#E5E5E5",
    secondary: "#A3A3A3",
    accent: "#F5F5F5",
    bg: "#171717",
    surface: "#262626",
    text: "#FAFAFA",
    muted: "#525252",
  },
};

export function applyTheme(slug: string) {
  const theme = themes[slug] || themes.aurora;
  const root = document.documentElement;
  root.style.setProperty("--lc-primary", theme.primary);
  root.style.setProperty("--lc-secondary", theme.secondary);
  root.style.setProperty("--lc-accent", theme.accent);
  root.style.setProperty("--lc-bg", theme.bg);
  root.style.setProperty("--lc-surface", theme.surface);
  root.style.setProperty("--lc-text", theme.text);
  root.style.setProperty("--lc-muted", theme.muted);
}
