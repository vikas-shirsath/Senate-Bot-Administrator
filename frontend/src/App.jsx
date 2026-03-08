import { useState, useRef, useEffect, useCallback } from "react";
import { supabase } from "./supabaseClient";
import Login from "./Login";
import "./App.css";

const API_BASE = "http://localhost:8000";

const QUICK_ACTIONS = [
  { icon: "🪪", label: "Ration card status", prompt: "Check ration card MH123456" },
  { icon: "📜", label: "Birth certificate", prompt: "Check birth certificate BC1021" },
  { icon: "📍", label: "Location lookup", prompt: "My pincode is 400001" },
  { icon: "📝", label: "File a grievance", prompt: "I want to file a grievance" },
  { icon: "🏠", label: "Housing eligibility", prompt: "Am I eligible for a housing scheme?" },
  { icon: "📋", label: "Apply for service", prompt: "I want to apply for ration card" },
];

const WELCOME_CHIPS = [
  "Check ration card MH123456",
  "My pincode is 400001",
  "Check birth certificate BC1021",
  "I want to apply for ration card",
  "Am I eligible for housing scheme?",
];

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
      } catch {
        // Silently fail — not critical
      }
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
      } catch {
        // offline
      }
    })();
  }, [session, authHeaders]);

  // ── Load messages when chat changes ─────────────
  useEffect(() => {
    if (!activeChatId || !session) {
      setMessages([]);
      return;
    }
    (async () => {
      try {
        const headers = await authHeaders();
        const resp = await fetch(`${API_BASE}/chats/${activeChatId}/messages`, { headers });
        const data = await resp.json();
        setMessages(data.map((m) => ({ ...m, time: m.created_at })));
      } catch {
        // offline
      }
    })();
  }, [activeChatId, session, authHeaders]);

  // ── Auto-scroll ─────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Check Ollama ────────────────────────────────
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
        method: "POST",
        headers,
        body: JSON.stringify({ title: "New Chat" }),
      });
      const chat = await resp.json();
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      setMessages([]);
    } catch {
      // offline
    }
  };

  // ── Send message ────────────────────────────────
  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    let chatId = activeChatId;

    // Auto-create a chat if none selected
    if (!chatId) {
      try {
        const headers = await authHeaders();
        const resp = await fetch(`${API_BASE}/chats`, {
          method: "POST",
          headers,
          body: JSON.stringify({ title: "New Chat" }),
        });
        const chat = await resp.json();
        chatId = chat.id;
        setChats((prev) => [chat, ...prev]);
        setActiveChatId(chatId);
      } catch {
        return;
      }
    }

    const newUserMessage = { role: "user", content: userMsg, time: new Date().toISOString() };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setLoading(true);

    try {
      const headers = await authHeaders();
      const resp = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ chat_id: chatId, message: userMsg }),
      });
      const data = await resp.json();
      const botMessage = {
        role: "assistant",
        content: data.reply,
        time: new Date().toISOString(),
        escalated: data.escalated || false,
      };
      setMessages((prev) => [...prev, botMessage]);

      // Update chat title in sidebar (first message auto-titles)
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId && c.title === "New Chat"
            ? { ...c, title: userMsg.slice(0, 60) + (userMsg.length > 60 ? "…" : "") }
            : c
        )
      );
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Unable to reach the server. Please make sure the FastAPI backend is running on port 8000.",
          time: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const deleteChat = async (chatId) => {
    try {
      const headers = await authHeaders();
      await fetch(`${API_BASE}/chats/${chatId}`, { method: "DELETE", headers });
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([]);
      }
    } catch {
      // offline
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setChats([]);
    setMessages([]);
    setActiveChatId(null);
  };

  // ── Render ──────────────────────────────────────
  if (authLoading) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: "center" }}>
          <div className="login-logo-icon" style={{ margin: "0 auto 16px" }}>🏛️</div>
          <p style={{ color: "var(--text-muted)" }}>Loading…</p>
        </div>
      </div>
    );
  }

  if (!session) return <Login />;

  const userName = session.user.user_metadata?.full_name || session.user.email?.split("@")[0] || "User";

  return (
    <div className="app">
      {/* ── Sidebar ────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">🏛️</div>
            <div className="logo-text">
              <h1>Senate Bot</h1>
              <p>Digital Governance Platform</p>
            </div>
          </div>
        </div>

        {/* New Chat button */}
        <div style={{ padding: "12px 12px 0" }}>
          <button className="new-chat-btn" onClick={createNewChat}>
            ＋ New Chat
          </button>
        </div>

        {/* Chat history */}
        <div className="chat-history">
          <h3>Chat History</h3>
          {chats.length === 0 && (
            <p style={{ padding: "0 8px", fontSize: 12, color: "var(--text-muted)" }}>
              No chats yet. Start a conversation!
            </p>
          )}
          {chats.map((c) => (
            <div
              key={c.id}
              className={`chat-history-item ${activeChatId === c.id ? "active" : ""}`}
              onClick={() => setActiveChatId(c.id)}
            >
              <span className="chat-history-title">💬 {c.title}</span>
              <button
                className="chat-delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteChat(c.id);
                }}
                title="Delete chat"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <h3>Quick Actions</h3>
          {QUICK_ACTIONS.map((qa, idx) => (
            <button
              key={idx}
              className="quick-btn"
              onClick={() => sendMessage(qa.prompt)}
              disabled={loading}
            >
              <span className="icon">{qa.icon}</span>
              {qa.label}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-avatar">👤</span>
            <span className="user-name">{userName}</span>
            <button className="logout-btn" onClick={handleLogout} title="Sign out">
              ⏻
            </button>
          </div>
          <div className="status-badge" style={{ marginTop: 8 }}>
            <span className={`status-dot ${ollamaStatus === "online" ? "" : "offline"}`} />
            Ollama LLM — {ollamaStatus === "online" ? "Connected" : ollamaStatus === "checking" ? "Checking…" : "Offline"}
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ─────────────────────── */}
      <main className="main">
        <header className="chat-header">
          <div className="chat-header-left">
            <h2>💬 Chat</h2>
            <span>llama3.1:8b</span>
          </div>
          <div className="header-actions">
            <button className="header-btn" title="New chat" onClick={createNewChat}>
              ＋
            </button>
          </div>
        </header>

        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon">🏛️</div>
              <h2>Welcome, {userName}!</h2>
              <p>
                Your AI-powered governance assistant. Ask me about ration card status,
                birth certificates, location info, scheme eligibility, or file a grievance.
              </p>
              <div className="welcome-chips">
                {WELCOME_CHIPS.map((chip, i) => (
                  <button key={i} className="welcome-chip" onClick={() => sendMessage(chip)}>
                    {chip}
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
                {msg.escalated && (
                  <div className="escalation-badge">⚠️ Escalation suggested — connect to human officer</div>
                )}
                <div className="msg-time">{formatTime(msg.time)}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="typing-indicator">
              <div
                className="msg-avatar"
                style={{
                  background: "linear-gradient(135deg, var(--accent), var(--accent-light))",
                  width: 32, height: 32, borderRadius: "var(--radius-xs)",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14,
                }}
              >
                🏛️
              </div>
              <div className="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about government services…"
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              title="Send message"
            >
              ➤
            </button>
          </div>
          <div className="input-hint">
            Senate Bot uses Llama 3.1 to assist with governance queries.
            Always verify information with official sources.
          </div>
        </div>
      </main>
    </div>
  );
}
