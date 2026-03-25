/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // These get overridden by CSS variables per theme
        lc: {
          primary: "var(--lc-primary)",
          secondary: "var(--lc-secondary)",
          accent: "var(--lc-accent)",
          bg: "var(--lc-bg)",
          surface: "var(--lc-surface)",
          text: "var(--lc-text)",
          muted: "var(--lc-muted)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
