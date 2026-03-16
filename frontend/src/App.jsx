import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { supabase } from "./supabaseClient";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import Login from "./Login";
import AdminPanel from "./AdminPanel";
import LanguageSelect from "./LanguageSelect";
import LanguageSwitcher from "./LanguageSwitcher";
import ThemeToggle from "./components/ThemeToggle";
import MessageBubble from "./components/MessageBubble";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import "./App.css";
import "./AdminPanel.css";

import {
  BookOpenText, Cake, MapPinHouse, MessageSquareWarning,
  HousePlus, Handshake, MessageCircle, PanelLeftClose,
  PanelLeftOpen, Plus, LogOut, Send, Menu, Trash2,
  ClipboardList, X, Clock, CheckCircle, XCircle, Loader,
  Mic, Square, BarChart3
} from "lucide-react";

import welcomeImg from "./assets/welcome.png";
import logoSvg from "./assets/logo.svg";

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

/* ═══════════════════════════════════════════════════
   Inner App (needs ThemeContext)
   ═══════════════════════════════════════════════════ */
function AppInner() {
  const { t, i18n } = useTranslation();

  // ── Language gate ───────────────────────────
  const [langChosen, setLangChosen] = useState(() => !!localStorage.getItem("language"));

  // ── Auth ────────────────────────────────────
  const [session, setSession] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // ── Chat ────────────────────────────────────
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [groqStatus, setGroqStatus] = useState("online");

  // ── UI ──────────────────────────────────────
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // ── Voice recording ────────────────────────
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // ── My Applications ─────────────────────────
  const [showApplications, setShowApplications] = useState(false);
  const [serviceRequests, setServiceRequests] = useState([]);

  // ── Analytics Dashboard ─────────────────────
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [loadingRequests, setLoadingRequests] = useState(false);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // ── Quick actions ───────────────────────────
  const QUICK_ACTIONS = [
    { icon: <BookOpenText size={16} />, labelKey: "sidebar.ration_status", promptKey: "welcome.chips.ration" },
    { icon: <Cake size={16} />, labelKey: "sidebar.birth_cert", promptKey: "welcome.chips.birth" },
    { icon: <MapPinHouse size={16} />, labelKey: "sidebar.location", promptKey: "welcome.chips.pincode" },
    { icon: <MessageSquareWarning size={16} />, labelKey: "sidebar.grievance", promptKey: "welcome.chips.grievance" },
    { icon: <HousePlus size={16} />, labelKey: "sidebar.housing", promptKey: "welcome.chips.eligibility" },
    { icon: <Handshake size={16} />, labelKey: "sidebar.apply_service", promptKey: "welcome.chips.apply" },
  ];

  // ── Helpers ─────────────────────────────────
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

  const authHeadersRaw = useCallback(
    async () => ({
      Authorization: `Bearer ${await getToken()}`,
    }),
    [getToken]
  );

  // ── Auth listener ───────────────────────────
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

  // ── Upsert user ─────────────────────────────
  useEffect(() => {
    if (!session) return;
    (async () => {
      try {
        const headers = await authHeaders();
        await fetch(`${API_BASE}/auth/callback`, {
          method: "POST", headers,
          body: JSON.stringify({
            name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0] || "",
          }),
        });
      } catch { /* silent */ }
    })();
  }, [session, authHeaders]);

  // ── Load chats ──────────────────────────────
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

  // ── Load messages on chat change or lang change ──
  useEffect(() => {
    if (!activeChatId || !session) { setMessages([]); return; }
    (async () => {
      try {
        const headers = await authHeaders();
        const resp = await fetch(
          `${API_BASE}/chats/${activeChatId}/messages?lang=${i18n.language}`,
          { headers }
        );
        const data = await resp.json();
        setMessages(data.map((m) => ({
          ...m,
          time: m.created_at,
        })));
      } catch { /* offline */ }
    })();
  }, [activeChatId, session, authHeaders, i18n.language]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  // ── Create new chat ─────────────────────────
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
      setMobileMenuOpen(false);
    } catch { /* offline */ }
  };

  // ── Ensure active chat exists ──────────────
  const ensureChatId = async () => {
    if (activeChatId) return activeChatId;
    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chats`, {
        method: "POST", headers,
        body: JSON.stringify({ title: "New Chat" }),
      });
      const chat = await resp.json();
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      return chat.id;
    } catch {
      return null;
    }
  };

  // ── Send text message ──────────────────────
  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    const chatId = await ensureChatId();
    if (!chatId) return;

    setMessages((prev) => [...prev, { role: "user", content: userMsg, time: new Date().toISOString(), input_type: "text" }]);
    setInput("");
    setLoading(true);

    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chat/text`, {
        method: "POST", headers,
        body: JSON.stringify({ chat_id: chatId, message: userMsg, preferred_language: i18n.language }),
      });
      const data = await resp.json();
      setMessages((prev) => [...prev, {
        role: "assistant", content: data.reply,
        time: new Date().toISOString(), escalated: data.escalated || false,
        audio_url: data.audio_base64 || null,
        input_type: "text",
      }]);
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId && c.title === "New Chat"
            ? { ...c, title: userMsg.slice(0, 50) + (userMsg.length > 50 ? "…" : "") }
            : c
        )
      );
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant", content: t("chat.server_error"), time: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // ── Voice recording ────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await sendVoice(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Mic access denied:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const sendVoice = async (audioBlob) => {
    if (loading) return;

    const chatId = await ensureChatId();
    if (!chatId) return;

    setMessages((prev) => [...prev, {
      role: "user", content: "🎤 Voice message…",
      time: new Date().toISOString(), input_type: "voice",
    }]);
    setLoading(true);

    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("chat_id", chatId);
      formData.append("preferred_language", i18n.language);

      const resp = await fetch(`${API_BASE}/chat/voice`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await resp.json();

      // Update the user message with transcribed text
      setMessages((prev) => {
        const updated = [...prev];
        const lastUserIdx = updated.findLastIndex((m) => m.role === "user" && m.input_type === "voice");
        if (lastUserIdx >= 0) {
          updated[lastUserIdx] = {
            ...updated[lastUserIdx],
            content: data.original_text || "🎤 Voice message",
          };
        }
        return [...updated, {
          role: "assistant", content: data.reply,
          time: new Date().toISOString(), escalated: data.escalated || false,
          audio_url: data.audio_base64 || null,
          input_type: "voice",
        }];
      });

      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId && c.title === "New Chat"
            ? { ...c, title: (data.original_text || "Voice").slice(0, 50) }
            : c
        )
      );
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant", content: t("chat.server_error"), time: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  // ── On-demand TTS (speaker icon) ────────────
  const requestTTS = async (text) => {
    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chat/tts`, {
        method: "POST", headers,
        body: JSON.stringify({ text, lang: i18n.language }),
      });
      const data = await resp.json();
      return data.audio_base64 || null;
    } catch {
      return null;
    }
  };

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

  // ── Fetch service requests ──────────────────
  const fetchServiceRequests = async () => {
    setShowApplications(true);
    setLoadingRequests(true);
    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/service-requests`, { headers });
      const data = await resp.json();
      setServiceRequests(data);
    } catch { setServiceRequests([]); }
    finally { setLoadingRequests(false); }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case "approved": return <CheckCircle size={14} className="status-icon approved" />;
      case "rejected": return <XCircle size={14} className="status-icon rejected" />;
      case "processing": return <Loader size={14} className="status-icon processing" />;
      default: return <Clock size={14} className="status-icon pending" />;
    }
  };

  const getStatusLabel = (status) => {
    const key = status?.toLowerCase() || "pending";
    return t(`applications.${key}`) || status;
  };

  // ── Render gates ────────────────────────────
  if (!langChosen) return <LanguageSelect onComplete={() => setLangChosen(true)} />;

  if (authLoading) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: "center" }}>
          <img src={logoSvg} alt="" style={{ width: 56, margin: "0 auto 16px" }} />
          <p style={{ color: "var(--text-muted)" }}>{t("auth.loading")}</p>
        </div>
      </div>
    );
  }

  if (!session) return <Login />;

  const userName = session.user.user_metadata?.full_name || session.user.email?.split("@")[0] || "User";
  const isAdmin = session.user.email === "admin@senate.gov";

  // Admin → AdminPanel
  if (isAdmin) {
    return (
      <AdminPanel
        getToken={getToken}
        userName={userName}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <div className="app">
      {/* Mobile overlay */}
      {mobileMenuOpen && <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} />}

      {/* ══ Sidebar ═════════════════════════════ */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""} ${mobileMenuOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <img src={logoSvg} alt="Logo" className="logo-img" />
            <div className="logo-text">
              <h1>{t("app.title")}</h1>
              <p>{t("app.subtitle")}</p>
            </div>
          </div>
          <button
            className="sidebar-collapse-btn"
            onClick={() => { setSidebarCollapsed(!sidebarCollapsed); setMobileMenuOpen(false); }}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        {/* New chat */}
        <div className="new-chat-wrap">
          <button className="new-chat-btn" onClick={createNewChat}>
            <span>{t("sidebar.new_chat")}</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="chat-history">
          <div className="section-label">{t("sidebar.chat_history")}</div>
          {chats.length === 0 && <div className="no-chats">{t("sidebar.no_chats")}</div>}
          {chats.map((c) => (
            <div key={c.id}
              className={`chat-history-item ${activeChatId === c.id ? "active" : ""}`}
              onClick={() => { setActiveChatId(c.id); setMobileMenuOpen(false); }}
            >
              <MessageCircle size={14} className="chat-history-icon" />
              <span className="chat-history-title">{c.title}</span>
              <button className="chat-delete-btn"
                onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }}>
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <div className="section-label">{t("sidebar.quick_actions")}</div>
          {QUICK_ACTIONS.map((qa, idx) => (
            <button key={idx} className="quick-btn"
              onClick={() => sendMessage(t(qa.promptKey))} disabled={loading}>
              <span className="q-icon">{qa.icon}</span>
              <span className="q-label">{t(qa.labelKey)}</span>
            </button>
          ))}
        </div>

        {/* My Applications Button */}
        <div style={{ padding: "0 8px 4px" }}>
          <button className="quick-btn my-apps-btn" onClick={fetchServiceRequests}>
            <span className="q-icon"><ClipboardList size={16} /></span>
            <span className="q-label">{t("sidebar.my_applications")}</span>
          </button>
        </div>



        {/* Footer */}
        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-avatar-icon">
              {userName.charAt(0).toUpperCase()}
            </span>
            <span className="user-name">{userName}</span>
            <button className="logout-btn" onClick={handleLogout} title={t("logout")}>
              <LogOut size={14} />
            </button>
          </div>
          <div className="status-badge">
            <span className="status-dot" />
            <span>Groq — {t("sidebar.ollama_connected")}</span>
          </div>
        </div>
      </aside>

      {/* ══ My Applications Panel ═══════════════ */}
      {showApplications && (
        <>
          <div className="apps-overlay" onClick={() => setShowApplications(false)} />
          <div className="apps-panel">
            <div className="apps-panel-header">
              <h3><ClipboardList size={18} /> {t("applications.title")}</h3>
              <button className="apps-close" onClick={() => setShowApplications(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="apps-panel-body">
              {loadingRequests ? (
                <div className="apps-loading">
                  <Loader size={24} className="status-icon processing" />
                </div>
              ) : serviceRequests.length === 0 ? (
                <div className="apps-empty">
                  <ClipboardList size={40} />
                  <p>{t("applications.no_requests")}</p>
                </div>
              ) : (
                serviceRequests.map((req) => (
                  <div key={req.id || req.request_id} className="app-card">
                    <div className="app-card-top">
                      <span className="app-card-id">#{req.request_id}</span>
                      <span className={`app-status-badge ${req.status?.toLowerCase() || "pending"}`}>
                        {getStatusIcon(req.status)}
                        {getStatusLabel(req.status)}
                      </span>
                    </div>
                    <div className="app-card-service">{req.service_type || req.service || "—"}</div>
                    <div className="app-card-date">
                      {t("applications.date")}: {new Date(req.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {/* ══ Main Content ════════════════════════ */}
      <main className="main">
      <>
        {/* Navbar */}
        <nav className="navbar">
          <div className="navbar-left">
            <button className="hamburger-btn" onClick={() => setMobileMenuOpen(true)}>
              <Menu size={18} />
            </button>
            <h2> {t("chat.heading")}</h2>
            <span className="navbar-badge">Groq · llama-3.1-8b</span>
          </div>
          <div className="navbar-right">
            <LanguageSwitcher />
            <ThemeToggle />
            <button className="header-btn" title="New chat" onClick={createNewChat}>
              <Plus size={16} />
            </button>
          </div>
        </nav>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <img src={welcomeImg} alt="Welcome" className="welcome-logo" />
              <h2>{t("welcome.heading_user", { name: userName })}</h2>
              <p>{t("welcome.description")}</p>
              <div className="welcome-chips">
                {["ration", "pincode", "birth", "grievance", "eligibility"].map((key) => (
                  <button key={key} className="welcome-chip"
                    onClick={() => sendMessage(t(`welcome.chips.${key}`))}>
                    {t(`welcome.chips.${key}`)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} renderMarkdown={renderMarkdown}
              formatTime={formatTime} t={t} onRequestTTS={requestTTS} />
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="typing-avatar">🏛️</div>
              <div className="typing-dots"><span></span><span></span><span></span></div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <input ref={inputRef} type="text" value={input}
              onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder={t("chat.placeholder")} disabled={loading || isRecording} />

            {/* Mic button */}
            <button
              className={`mic-btn ${isRecording ? "recording" : ""}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
              title={isRecording ? "Stop recording" : "Start voice input"}
            >
              {isRecording ? <Square size={16} /> : <Mic size={16} />}
            </button>

            <button className="send-btn" onClick={() => sendMessage()}
              disabled={!input.trim() || loading || isRecording}>
              <Send size={16} />
            </button>
          </div>
          {isRecording && (
            <div className="recording-indicator">
              <span className="rec-dot"></span>
              <span>{t("chat.recording") || "Recording…"}</span>
            </div>
          )}
          <div className="input-hint">{t("app.disclaimer")}</div>
        </div>
      </>
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Root with ThemeProvider
   ═══════════════════════════════════════════════════ */
export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  );
}
