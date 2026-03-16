import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Shield, User } from "lucide-react";
import logoSvg from "./assets/logo.svg";
import "./Login.css";

export default function RoleSelect({ onSelect }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState(null);

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 440 }}>
        <div className="login-logo">
          <img src={logoSvg} alt="Logo" className="login-logo-img" />
          <h1>{t("auth.login_title")}</h1>
          <p>Choose how you'd like to continue</p>
        </div>

        <div className="role-options">
          <button
            className={`role-card ${selected === "user" ? "active" : ""}`}
            onClick={() => setSelected("user")}
          >
            <User size={28} />
            <div className="role-card-text">
              <strong>Citizen</strong>
              <span>Access government services, track applications</span>
            </div>
          </button>

          <button
            className={`role-card ${selected === "admin" ? "active" : ""}`}
            onClick={() => setSelected("admin")}
          >
            <Shield size={28} />
            <div className="role-card-text">
              <strong>Administrator</strong>
              <span>Manage users, approve requests, view analytics</span>
            </div>
          </button>
        </div>

        <button
          className="login-btn submit"
          disabled={!selected}
          onClick={() => onSelect(selected)}
          style={{ marginTop: 16 }}
        >
          Continue as {selected === "admin" ? "Admin" : "Citizen"}
        </button>
      </div>
    </div>
  );
}
