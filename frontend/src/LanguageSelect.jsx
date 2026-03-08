import { useState } from "react";
import { useTranslation } from "react-i18next";
import "./LanguageSelect.css";

const LANGUAGES = [
  { code: "en", label: "English", native: "English", flag: "🇬🇧" },
  { code: "hi", label: "Hindi", native: "हिंदी", flag: "🇮🇳" },
  { code: "mr", label: "Marathi", native: "मराठी", flag: "🇮🇳" },
  { code: "te", label: "Telugu", native: "తెలుగు", flag: "🇮🇳" },
];

export default function LanguageSelect({ onComplete }) {
  const { i18n } = useTranslation();
  const [selected, setSelected] = useState(i18n.language || "en");

  const handleContinue = () => {
    i18n.changeLanguage(selected);
    localStorage.setItem("language", selected);
    onComplete();
  };

  return (
    <div className="lang-page">
      <div className="lang-card">
        <div className="lang-logo-icon">🏛️</div>
        <h1 className="lang-title">Choose Your Language</h1>
        <p className="lang-subtitle">Select your preferred language to continue</p>

        <div className="lang-grid">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              className={`lang-option ${selected === lang.code ? "active" : ""}`}
              onClick={() => setSelected(lang.code)}
            >
              <span className="lang-flag">{lang.flag}</span>
              <span className="lang-native">{lang.native}</span>
              <span className="lang-english">{lang.label}</span>
            </button>
          ))}
        </div>

        <button className="lang-continue" onClick={handleContinue}>
          Continue →
        </button>
      </div>
    </div>
  );
}
