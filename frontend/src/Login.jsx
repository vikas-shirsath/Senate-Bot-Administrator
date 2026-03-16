import { useState } from "react";
import { useTranslation } from "react-i18next";
import { supabase } from "./supabaseClient";
import LanguageSwitcher from "./LanguageSwitcher";
import ThemeToggle from "./components/ThemeToggle";
import logoSvg from "./assets/logo.svg";
import { Shield, ArrowLeft } from "lucide-react";
import "./Login.css";

export default function Login({ adminMode = false, onBack }) {
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
          email, password,
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
      <div className={`login-card ${adminMode ? "admin-mode" : ""}`}>
        <div style={{ position: "absolute", top: 14, right: 14, display: "flex", gap: 6 }}>
          <LanguageSwitcher />
          <ThemeToggle />
        </div>

        {/* Back to role select */}
        {onBack && (
          <button className="login-back-btn" onClick={onBack}>
            <ArrowLeft size={15} /> Change role
          </button>
        )}

        <div className="login-logo">
          {adminMode ? (
            <div className="admin-shield-icon">
              <Shield size={32} />
            </div>
          ) : (
            <img src={logoSvg} alt="Logo" className="login-logo-img" />
          )}
          <h1>
            {adminMode ? "Administrator Portal" : t("auth.login_title")}
          </h1>
          <p>
            {adminMode
              ? "Restricted access — authorised personnel only"
              : t("auth.login_subtitle")}
          </p>
        </div>

        {/* Google login — citizen only */}
        {!adminMode && (
          <>
            <button className="login-btn google" onClick={handleGoogleLogin}>
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" />
              {t("auth.google_btn")}
            </button>
            <div className="login-divider">{t("auth.or_divider")}</div>
          </>
        )}

        <form onSubmit={handleEmailAuth}>
          <div className="login-field">
            <label htmlFor="email">{t("auth.email_label")}</label>
            <input id="email" type="email" placeholder={adminMode ? "admin@senate.gov" : t("auth.email_placeholder")}
              value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="login-field">
            <label htmlFor="password">{t("auth.password_label")}</label>
            <input id="password" type="password" placeholder={t("auth.password_placeholder")}
              value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
          </div>
          <button className={`login-btn submit ${adminMode ? "admin-submit" : ""}`} type="submit" disabled={loading}>
            {loading ? t("auth.loading_btn") : adminMode ? "Sign in as Admin" : isSignUp ? t("auth.signup_btn") : t("auth.signin_btn")}
          </button>
        </form>

        {error && <div className="login-error">{error}</div>}

        {/* Sign-up toggle — citizen only */}
        {!adminMode && (
          <div className="login-footer">
            {isSignUp ? t("auth.has_account") : t("auth.no_account")}{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setIsSignUp(!isSignUp); setError(""); }}>
              {isSignUp ? t("auth.signin_btn") : t("auth.signup_btn")}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
