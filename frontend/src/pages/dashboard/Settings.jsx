import { ACCENTS } from "../../context/ThemeContext";
import { useTheme } from "../../context/useTheme";
import "./Account.css";

const THEMES = [
  { id: "dark", label: "Dark", hint: "Easier on the eyes in low light" },
  { id: "light", label: "Light", hint: "Bright, paper-like workspace" },
];

export default function Settings() {
  const { theme, setTheme, accent, setAccent } = useTheme();

  return (
    <div className="account">
      <div>
        <h1 className="account__title">Settings</h1>
        <p className="account__subtitle">Choose how TrustShare looks. Changes apply instantly and are saved on this device.</p>
      </div>

      <section className="account__card">
        <h2>Appearance</h2>
        <p className="account__card-hint">Pick a mode and a colour palette.</p>

        <p className="appearance__section-label">Mode</p>
        <div className="appearance__group">
          {THEMES.map((option) => (
            <button
              key={option.id}
              type="button"
              className="appearance__option"
              aria-pressed={theme === option.id}
              onClick={() => setTheme(option.id)}
            >
              <span className="appearance__label">{option.label}</span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{option.hint}</span>
            </button>
          ))}
        </div>

        <p className="appearance__section-label">Palette</p>
        <div className="appearance__group">
          {ACCENTS.map((option) => (
            <button
              key={option.id}
              type="button"
              className="appearance__option"
              aria-pressed={accent === option.id}
              onClick={() => setAccent(option.id)}
            >
              <span className="appearance__swatches">
                {option.swatch.map((color) => (
                  <span key={color} className="appearance__swatch" style={{ background: color }} />
                ))}
              </span>
              <span className="appearance__label">{option.label}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
