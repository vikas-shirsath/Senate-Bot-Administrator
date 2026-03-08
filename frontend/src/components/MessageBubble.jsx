export default function MessageBubble({ msg, renderMarkdown, formatTime, t }) {
  const isUser = msg.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "bot"}`}>
      <div className={`msg-avatar ${isUser ? "user-av" : "bot-av"}`}>
        {isUser ? "👤" : "🏛️"}
      </div>
      <div className="msg-body">
        <div className="msg-bubble">
          {msg.content.split("\n").map((line, j, arr) => (
            <span key={j}>
              {renderMarkdown(line)}
              {j < arr.length - 1 && <br />}
            </span>
          ))}
        </div>
        {msg.escalated && (
          <div className="escalation-badge">{t("chat.escalation")}</div>
        )}
        <div className="msg-time">{formatTime(msg.time)}</div>
      </div>
    </div>
  );
}
