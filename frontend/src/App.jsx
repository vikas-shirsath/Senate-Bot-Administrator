import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

const QUICK_ACTIONS = [
  { icon: "🪪", label: "Ration card status", prompt: "Check ration card MH123456" },
  { icon: "📜", label: "Birth certificate", prompt: "Check birth certificate BC1021" },
  { icon: "📍", label: "Location lookup", prompt: "My pincode is 400001" },
  { icon: "📝", label: "File a grievance", prompt: "I want to file a grievance" },
  { icon: "🏠", label: "Housing eligibility", prompt: "Am I eligible for a housing scheme?" },
];

const WELCOME_CHIPS = [
  "Check ration card MH123456",
  "My pincode is 400001",
  "Check birth certificate BC1021",
  "I want to register a grievance",
  "Am I eligible for housing scheme?",
];

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** Turn **bold** markdown into <strong> tags */
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
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState("checking");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Check Ollama status
  useEffect(() => {
    fetch("http://localhost:11434/api/tags")
      .then((r) => (r.ok ? setOllamaStatus("online") : setOllamaStatus("offline")))
      .catch(() => setOllamaStatus("offline"));
  }, []);

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    const newUserMessage = { role: "user", content: userMsg, time: new Date() };
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const conversation = updatedMessages.map(({ role, content }) => ({ role, content }));
      const resp = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, conversation }),
      });
      const data = await resp.json();
      const botMessage = {
        role: "assistant",
        content: data.reply,
        time: new Date(),
        escalated: data.escalated || false,
        service_result: data.service_result || null,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠️ Unable to reach the server. Please make sure the FastAPI backend is running on port 8000.",
          time: new Date(),
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

  const clearChat = () => {
    setMessages([]);
  };

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
          <div className="status-badge">
            <span className={`status-dot ${ollamaStatus === "online" ? "" : "offline"}`} />
            Ollama LLM —{" "}
            {ollamaStatus === "online"
              ? "Connected"
              : ollamaStatus === "checking"
              ? "Checking..."
              : "Offline"}
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ─────────────────────── */}
      <main className="main">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <h2>💬 Chat</h2>
            <span>llama3.1:8b</span>
          </div>
          <div className="header-actions">
            <button className="header-btn" title="Clear chat" onClick={clearChat}>
              🗑️
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon">🏛️</div>
              <h2>Welcome to Senate Bot</h2>
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
              <div className="msg-avatar">
                {msg.role === "user" ? "👤" : "🏛️"}
              </div>
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
                  <div className="escalation-badge">
                    ⚠️ Escalation suggested — connect to human officer
                  </div>
                )}
                <div className="msg-time">{formatTime(msg.time)}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="msg-avatar" style={{
                background: "linear-gradient(135deg, var(--accent), var(--accent-light))",
                width: 32, height: 32, borderRadius: "var(--radius-xs)",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14
              }}>
                🏛️
              </div>
              <div className="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
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
