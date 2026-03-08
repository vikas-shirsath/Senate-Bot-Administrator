import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import "./LanguageSelect.css";

const LANGUAGES = [
  { code: "en", native: "English" },
  { code: "hi", native: "हिंदी" },
  { code: "mr", native: "मराठी" },
  { code: "te", native: "తెలుగు" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const changeLang = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem("language", code);
    setOpen(false);
  };

  const current = LANGUAGES.find((l) => l.code === i18n.language) || LANGUAGES[0];

  return (
    <div className="lang-switcher" ref={ref}>
      <button className="lang-switcher-btn" onClick={() => setOpen(!open)}>
        🌐 {current.native}
      </button>
      {open && (
        <div className="lang-dropdown">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              className={`lang-dropdown-item ${i18n.language === lang.code ? "active" : ""}`}
              onClick={() => changeLang(lang.code)}
            >
              {lang.native}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
