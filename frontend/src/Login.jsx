import { useState } from "react";
import { useTranslation } from "react-i18next";
import { supabase } from "./supabaseClient";
import LanguageSwitcher from "./LanguageSwitcher";
import "./Login.css";

export default function Login() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleLogin = async () => {
    setError("");
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
    if (error) setError(error.message);
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: window.location.origin },
        });
        if (error) throw error;
        setError(t("auth.check_email"));
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Language switcher in top-right corner */}
        <div style={{ position: "absolute", top: 16, right: 16 }}>
          <LanguageSwitcher />
        </div>

        <div className="login-logo">
          <div className="login-logo-icon">🏛️</div>
          <h1>{t("auth.login_title")}</h1>
          <p>{t("auth.login_subtitle")}</p>
        </div>

        <button className="login-btn google" onClick={handleGoogleLogin}>
          <img
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
            alt="Google"
          />
          {t("auth.google_btn")}
        </button>

        <div className="login-divider">{t("auth.or_divider")}</div>

        <form onSubmit={handleEmailAuth}>
          <div className="login-field">
            <label htmlFor="email">{t("auth.email_label")}</label>
            <input
              id="email"
              type="email"
              placeholder={t("auth.email_placeholder")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="login-field">
            <label htmlFor="password">{t("auth.password_label")}</label>
            <input
              id="password"
              type="password"
              placeholder={t("auth.password_placeholder")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <button className="login-btn submit" type="submit" disabled={loading}>
            {loading ? t("auth.loading_btn") : isSignUp ? t("auth.signup_btn") : t("auth.signin_btn")}
          </button>
        </form>

        {error && <div className="login-error">{error}</div>}

        <div className="login-footer">
          {isSignUp ? t("auth.has_account") : t("auth.no_account")}{" "}
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); setIsSignUp(!isSignUp); setError(""); }}
            style={{ color: "var(--accent-light)" }}
          >
            {isSignUp ? t("auth.signin_btn") : t("auth.signup_btn")}
          </a>
        </div>
      </div>
    </div>
  );
}
