import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { supabase } from "./supabaseClient";
import Login from "./Login";
import LanguageSelect from "./LanguageSelect";
import LanguageSwitcher from "./LanguageSwitcher";
import "./App.css";
import { BookOpenText } from 'lucide-react';
import { Cake } from 'lucide-react';
import { MapPinHouse } from 'lucide-react';
import { MessageSquareWarning } from 'lucide-react';
import { HousePlus } from 'lucide-react';
import { Handshake } from 'lucide-react';
const API_BASE = "http://localhost:8000";

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function renderMarkdown(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

export default function App() {
  const { t, i18n } = useTranslation();

  // ── Language gate ───────────────────────────────
  const [langChosen, setLangChosen] = useState(() => !!localStorage.getItem("language"));

  // ── Auth state ──────────────────────────────────
  const [session, setSession] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // ── Chat state ──────────────────────────────────
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState("checking");

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // ── Quick actions (translated) ──────────────────
  const QUICK_ACTIONS = [
    { icon: <BookOpenText />, labelKey: "sidebar.ration_status", prompt: t("welcome.chips.ration") },
    { icon: <Cake />, labelKey: "sidebar.birth_cert", prompt: t("welcome.chips.birth") },
    { icon: <MapPinHouse />, labelKey: "sidebar.location", prompt: t("welcome.chips.pincode") },
    { icon: <MessageSquareWarning />, labelKey: "sidebar.grievance", prompt: t("welcome.chips.grievance") },
    { icon: <HousePlus />, labelKey: "sidebar.housing", prompt: t("welcome.chips.eligibility") },
    { icon: <Handshake />, labelKey: "sidebar.apply_service", prompt: t("welcome.chips.apply") },
  ];

  const WELCOME_CHIPS = [
    { key: "ration", label: t("welcome.chips.ration") },
    { key: "pincode", label: t("welcome.chips.pincode") },
    { key: "birth", label: t("welcome.chips.birth") },
    { key: "grievance", label: t("welcome.chips.grievance") },
    { key: "eligibility", label: t("welcome.chips.eligibility") },
  ];

  // ── Helpers ─────────────────────────────────────
  const getToken = useCallback(async () => {
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || "";
  }, []);

  const authHeaders = useCallback(
    async () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${await getToken()}`,
    }),
    [getToken]
  );

  // ── Auth listener ───────────────────────────────
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setAuthLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setAuthLoading(false);
    });
    return () => subscription.unsubscribe();
  }, []);

  // ── Upsert user on login ────────────────────────
  useEffect(() => {
    if (!session) return;
    (async () => {
      try {
        const headers = await authHeaders();
        await fetch(`${API_BASE}/auth/callback`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0] || "",
          }),
        });
      } catch { /* silent */ }
    })();
  }, [session, authHeaders]);

  // ── Load chats ──────────────────────────────────
  useEffect(() => {
    if (!session) return;
    (async () => {
      try {
        const headers = await authHeaders();
        const resp = await fetch(`${API_BASE}/chats`, { headers });
        const data = await resp.json();
        setChats(data);
      } catch { /* offline */ }
    })();
  }, [session, authHeaders]);

  // ── Load messages when chat changes ─────────────
  useEffect(() => {
    if (!activeChatId || !session) { setMessages([]); return; }
    (async () => {
      try {
        const headers = await authHeaders();
        const resp = await fetch(`${API_BASE}/chats/${activeChatId}/messages`, { headers });
        const data = await resp.json();
        setMessages(data.map((m) => ({ ...m, time: m.created_at })));
      } catch { /* offline */ }
    })();
  }, [activeChatId, session, authHeaders]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  useEffect(() => {
    fetch("http://localhost:11434/api/tags")
      .then((r) => (r.ok ? setOllamaStatus("online") : setOllamaStatus("offline")))
      .catch(() => setOllamaStatus("offline"));
  }, []);

  // ── Create new chat ─────────────────────────────
  const createNewChat = async () => {
    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chats`, {
        method: "POST", headers,
        body: JSON.stringify({ title: "New Chat" }),
      });
      const chat = await resp.json();
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      setMessages([]);
    } catch { /* offline */ }
  };

  // ── Send message (with language info) ───────────
  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    let chatId = activeChatId;
    if (!chatId) {
      try {
        const headers = await authHeaders();
        const resp = await fetch(`${API_BASE}/chats`, {
          method: "POST", headers,
          body: JSON.stringify({ title: "New Chat" }),
        });
        const chat = await resp.json();
        chatId = chat.id;
        setChats((prev) => [chat, ...prev]);
        setActiveChatId(chatId);
      } catch { return; }
    }

    setMessages((prev) => [...prev, { role: "user", content: userMsg, time: new Date().toISOString() }]);
    setInput("");
    setLoading(true);

    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chat`, {
        method: "POST", headers,
        body: JSON.stringify({
          chat_id: chatId,
          message: userMsg,
          preferred_language: i18n.language,
        }),
      });
      const data = await resp.json();
      setMessages((prev) => [...prev, {
        role: "assistant", content: data.reply,
        time: new Date().toISOString(), escalated: data.escalated || false,
      }]);
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId && c.title === "New Chat"
            ? { ...c, title: userMsg.slice(0, 60) + (userMsg.length > 60 ? "…" : "") }
            : c
        )
      );
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant", content: t("chat.server_error"),
        time: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  const deleteChat = async (chatId) => {
    try {
      const headers = await authHeaders();
      await fetch(`${API_BASE}/chats/${chatId}`, { method: "DELETE", headers });
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (activeChatId === chatId) { setActiveChatId(null); setMessages([]); }
    } catch { /* offline */ }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null); setChats([]); setMessages([]); setActiveChatId(null);
  };

  // ── Render gates ────────────────────────────────
  if (!langChosen) return <LanguageSelect onComplete={() => setLangChosen(true)} />;

  if (authLoading) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: "center" }}>
          <div className="login-logo-icon" style={{ margin: "0 auto 16px" }}>🏛️</div>
          <p style={{ color: "var(--text-muted)" }}>{t("auth.loading")}</p>
        </div>
      </div>
    );
  }

  if (!session) return <Login />;

  const userName = session.user.user_metadata?.full_name || session.user.email?.split("@")[0] || "User";

  const ollamaLabel = ollamaStatus === "online"
    ? t("sidebar.ollama_connected")
    : ollamaStatus === "checking"
      ? t("sidebar.ollama_checking")
      : t("sidebar.ollama_offline");

  return (
    <div className="app">
      {/* ── Sidebar ────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">🏛️</div>
            <div className="logo-text">
              <h1>{t("app.title")}</h1>
              <p>{t("app.subtitle")}</p>
            </div>
          </div>
        </div>

        <div style={{ padding: "12px 12px 0" }}>
          <button className="new-chat-btn" onClick={createNewChat}>{t("sidebar.new_chat")}</button>
        </div>

        <div className="chat-history">
          <h3>{t("sidebar.chat_history")}</h3>
          {chats.length === 0 && (
            <p style={{ padding: "0 8px", fontSize: 12, color: "var(--text-muted)" }}>{t("sidebar.no_chats")}</p>
          )}
          {chats.map((c) => (
            <div key={c.id} className={`chat-history-item ${activeChatId === c.id ? "active" : ""}`}
              onClick={() => setActiveChatId(c.id)}>
              <span className="chat-history-title">💬 {c.title}</span>
              <button className="chat-delete-btn"
                onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} title="Delete">×</button>
            </div>
          ))}
        </div>

        <div className="quick-actions">
          <h3>{t("sidebar.quick_actions")}</h3>
          {QUICK_ACTIONS.map((qa, idx) => (
            <button key={idx} className="quick-btn" onClick={() => sendMessage(qa.prompt)} disabled={loading}>
              <span className="icon">{qa.icon}</span>
              {t(qa.labelKey)}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-avatar">👤</span>
            <span className="user-name">{userName}</span>
            <button className="logout-btn" onClick={handleLogout} title={t("logout")}>⏻</button>
          </div>
          <div className="status-badge" style={{ marginTop: 8 }}>
            <span className={`status-dot ${ollamaStatus === "online" ? "" : "offline"}`} />
            Ollama LLM — {ollamaLabel}
          </div>
        </div>
      </aside>

      {/* ── Main ───────────────────────────────── */}
      <main className="main">
        <header className="chat-header">
          <div className="chat-header-left">
            <h2>{t("chat.heading")}</h2>
            <span>{t("app.model_badge")}</span>
          </div>
          <div className="header-actions">
            <LanguageSwitcher />
            <button className="header-btn" title="New chat" onClick={createNewChat}>{t("chat.new_chat_btn")}</button>
          </div>
        </header>

        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon">🏛️</div>
              <h2>{t("welcome.heading_user", { name: userName })}</h2>
              <p>{t("welcome.description")}</p>
              <div className="welcome-chips">
                {WELCOME_CHIPS.map((chip) => (
                  <button key={chip.key} className="welcome-chip" onClick={() => sendMessage(chip.label)}>
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role === "user" ? "user" : "bot"}`}>
              <div className="msg-avatar">{msg.role === "user" ? "👤" : "🏛️"}</div>
              <div>
                <div className="msg-bubble">
                  {msg.content.split("\n").map((line, j) => (
                    <span key={j}>
                      {renderMarkdown(line)}
                      {j < msg.content.split("\n").length - 1 && <br />}
                    </span>
                  ))}
                </div>
                {msg.escalated && <div className="escalation-badge">{t("chat.escalation")}</div>}
                <div className="msg-time">{formatTime(msg.time)}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="msg-avatar" style={{
                background: "linear-gradient(135deg, var(--accent), var(--accent-light))",
                width: 32, height: 32, borderRadius: "var(--radius-xs)",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14,
              }}>🏛️</div>
              <div className="typing-dots"><span></span><span></span><span></span></div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            <input ref={inputRef} type="text" value={input}
              onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder={t("chat.placeholder")} disabled={loading} />
            <button className="send-btn" onClick={() => sendMessage()}
              disabled={!input.trim() || loading} title="Send">➤</button>
          </div>
          <div className="input-hint">{t("app.disclaimer")}</div>
        </div>
      </main>
    </div>
  );
}
