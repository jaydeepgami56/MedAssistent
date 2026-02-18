import { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext();

const lightPalette = {
  "--bg-primary": "#ffffff",
  "--bg-secondary": "#f8f9fa",
  "--bg-tertiary": "#f1f3f5",
  "--text-primary": "#1a1a2e",
  "--text-secondary": "#6b7280",
  "--text-muted": "#9ca3af",
  "--border": "#e5e7eb",
  "--border-light": "#f0f0f0",
  "--card-bg": "#ffffff",
  "--card-shadow": "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
  "--card-hover-shadow": "0 4px 12px rgba(0,0,0,0.1)",
  "--nav-bg": "#ffffff",
  "--nav-border": "#e5e7eb",
  "--input-bg": "#ffffff",
  "--input-border": "#d1d5db",
  "--input-border-focus": "#00b4d8",
  "--user-msg-bg": "#1a1a2e",
  "--user-msg-text": "#ffffff",
  "--assistant-msg-bg": "transparent",
  "--assistant-msg-border": "transparent",
  "--system-msg-bg": "#f1f3f5",
  "--error-bg": "#fef2f2",
  "--error-border": "#fecaca",
  "--brand-color": "#00b4d8",
  "--brand-text": "#0891b2",
  "--accent-bg-opacity": "0.06",
  "--active-nav-bg": "#f0f9ff",
  "--active-nav-border": "#00b4d8",
  "--hover-bg": "#f9fafb",
  "--scrollbar-thumb": "#d1d5db",
  "--scrollbar-track": "#f1f3f5",
};

const darkPalette = {
  "--bg-primary": "#0a1628",
  "--bg-secondary": "#0e1a2e",
  "--bg-tertiary": "#1a2f4a",
  "--text-primary": "#e0e8f0",
  "--text-secondary": "#8899aa",
  "--text-muted": "#667788",
  "--border": "#1e3a5f",
  "--border-light": "rgba(30,58,95,0.27)",
  "--card-bg": "#0e1a2e",
  "--card-shadow": "0 1px 3px rgba(0,0,0,0.3)",
  "--card-hover-shadow": "0 4px 12px rgba(0,0,0,0.4)",
  "--nav-bg": "#0d1b2a",
  "--nav-border": "#1e3a5f",
  "--input-bg": "#0a1628",
  "--input-border": "#1e3a5f",
  "--input-border-focus": "#00b4d8",
  "--user-msg-bg": "#1a1a2e",
  "--user-msg-text": "#ffffff",
  "--assistant-msg-bg": "#0e1a2e",
  "--assistant-msg-border": "#1e3a5f",
  "--system-msg-bg": "#1a2f4a",
  "--error-bg": "#1a0505",
  "--error-border": "rgba(239,68,68,0.2)",
  "--brand-color": "#00b4d8",
  "--brand-text": "#00b4d8",
  "--accent-bg-opacity": "0.08",
  "--active-nav-bg": "rgba(0,180,216,0.08)",
  "--active-nav-border": "#00b4d8",
  "--hover-bg": "rgba(255,255,255,0.03)",
  "--scrollbar-thumb": "#1e3a5f",
  "--scrollbar-track": "#0e1a2e",
};

function applyTheme(theme) {
  const palette = theme === "dark" ? darkPalette : lightPalette;
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  for (const [key, value] of Object.entries(palette)) {
    root.style.setProperty(key, value);
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem("medassist-theme") || "light";
    } catch {
      return "light";
    }
  });

  useEffect(() => {
    applyTheme(theme);
    try {
      localStorage.setItem("medassist-theme", theme);
    } catch {}
  }, [theme]);

  const toggleTheme = () => setTheme(t => (t === "light" ? "dark" : "light"));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
