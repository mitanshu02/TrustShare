import { useEffect, useState } from "react";
import { ThemeContext } from "./themeContextObject";

const THEME_KEY = "trustshare_theme";
const ACCENT_KEY = "trustshare_accent";

export const ACCENTS = [
  { id: "brass", label: "Brass & Teal", swatch: ["#c9974c", "#4f9186"] },
  { id: "indigo", label: "Indigo & Mint", swatch: ["#5b6fd8", "#02c39a"] },
  { id: "crimson", label: "Crimson Seal", swatch: ["#b3542f", "#7a8471"] },
];

function readStored(key, allowed, fallback) {
  try {
    const value = localStorage.getItem(key);
    return allowed.includes(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => readStored(THEME_KEY, ["dark", "light"], "dark"));
  const [accent, setAccent] = useState(() =>
    readStored(ACCENT_KEY, ACCENTS.map((a) => a.id), "brass")
  );

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    // "brass" is the default palette defined on :root, so no attribute is needed.
    if (accent === "brass") root.removeAttribute("data-accent");
    else root.setAttribute("data-accent", accent);

    try {
      localStorage.setItem(THEME_KEY, theme);
      localStorage.setItem(ACCENT_KEY, accent);
    } catch {
      // Storage can be blocked (private mode); the choice just won't persist.
    }
  }, [theme, accent]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, accent, setAccent }}>
      {children}
    </ThemeContext.Provider>
  );
}
