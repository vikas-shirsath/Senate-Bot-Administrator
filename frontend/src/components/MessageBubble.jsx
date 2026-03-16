import { useState, useRef } from "react";
import { Volume2, Loader } from "lucide-react";

export default function MessageBubble({ msg, renderMarkdown, formatTime, t, onRequestTTS }) {
  const isUser = msg.role === "user";
  const isVoice = msg.input_type === "voice";
  const hasAudio = msg.audio_url && msg.audio_url.startsWith("data:audio");

  // On-demand TTS state
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsAudio, setTtsAudio] = useState(null);
  const audioRef = useRef(null);

  const handleSpeakerClick = async () => {
    // If we already have audio (auto or previously fetched), play it
    if (hasAudio) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
      }
      return;
    }
    if (ttsAudio) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
      }
      return;
    }

    // Fetch TTS from backend
    if (onRequestTTS) {
      setTtsLoading(true);
      try {
        const audioSrc = await onRequestTTS(msg.content);
        if (audioSrc) {
          setTtsAudio(audioSrc);
          // Auto-play after loading
          setTimeout(() => {
            if (audioRef.current) audioRef.current.play();
          }, 100);
        }
      } finally {
        setTtsLoading(false);
      }
    }
  };

  const audioSrc = hasAudio ? msg.audio_url : ttsAudio;

  return (
    <div className={`message-row ${isUser ? "user" : "bot"}`}>
      <div className={`msg-avatar ${isUser ? "user-av" : "bot-av"}`}>
        {isUser ? "👤" : "🏛️"}
      </div>
      <div className="msg-body">
        <div className="msg-bubble">
          {isVoice && isUser && <span className="voice-badge">🎤</span>}
          {msg.content.split("\n").map((line, j, arr) => (
            <span key={j}>
              {renderMarkdown(line)}
              {j < arr.length - 1 && <br />}
            </span>
          ))}
        </div>

        {/* Audio player — shown when audio is available (auto or on-demand) */}
        {audioSrc && (
          <div className="audio-player-wrap">
            <audio ref={audioRef} controls preload="none" className="msg-audio">
              <source src={audioSrc} type="audio/wav" />
            </audio>
          </div>
        )}

        {/* Bottom row: time + speaker icon for bot messages */}
        <div className="msg-footer">
          <div className="msg-time">{formatTime(msg.time)}</div>
          {!isUser && (
            <button
              className={`speak-btn ${ttsLoading ? "loading" : ""}`}
              onClick={handleSpeakerClick}
              disabled={ttsLoading}
              title="Listen"
            >
              {ttsLoading ? <Loader size={13} className="spin" /> : <Volume2 size={13} />}
            </button>
          )}
        </div>

        {msg.escalated && (
          <div className="escalation-badge">{t("chat.escalation")}</div>
        )}
      </div>
    </div>
  );
}
