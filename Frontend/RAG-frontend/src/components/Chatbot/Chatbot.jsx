import { useState, useRef, useEffect } from "react";
import {
  chatWithPaper,
  clearChatSession,
  paperStart,
  paperChat,
  clearPaperSession,
} from "../../services/api";
import "./Chatbot.css";

export default function PaperChatbot({ paper }) {
  const isGlobalMode = !paper;

  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const bottomRef    = useRef(null);
  const textareaRef  = useRef(null);
  const sessionIdRef = useRef(null);

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Keep ref in sync with state ───────────────────────────────────────────
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // ── Paper mode: start session + get opening message on mount ─────────────
  useEffect(() => {
    if (isGlobalMode) return;
    initPaperSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (!sessionIdRef.current) return;
      if (isGlobalMode) {
        clearChatSession(sessionIdRef.current).catch(() => {});
      } else {
        clearPaperSession(sessionIdRef.current).catch(() => {});
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Start (or restart) a paper session ───────────────────────────────────
  const initPaperSession = async () => {
    setLoading(true);
    setMessages([]);
    try {
      const data = await paperStart(paper.id);
      setSessionId(data.session_id);
      setMessages([{ role: "assistant", content: data.opening_message }]);
    } catch (err) {
      setMessages([{ role: "error", content: "Could not load paper session — please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  // ── Auto-resize textarea ──────────────────────────────────────────────────
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }
  };

  // ── Core send logic ───────────────────────────────────────────────────────
  const sendMessage = async () => {
    const userText = input.trim();
    if (!userText || loading) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setLoading(true);

    try {
      let answer;

      if (isGlobalMode) {
        const data = await chatWithPaper({ message: userText, sessionId });
        if (!sessionId) setSessionId(data.session_id);
        answer = data.answer;
      } else {
        const data = await paperChat({ sessionId, message: userText });
        answer = data.answer;
      }

      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "error", content: "Something went wrong — please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ── Enter to send, Shift+Enter for newline ────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ── Reset ─────────────────────────────────────────────────────────────────
  const resetChat = () => {
    if (sessionId) {
      if (isGlobalMode) {
        clearChatSession(sessionId).catch(() => {});
      } else {
        clearPaperSession(sessionId).catch(() => {});
      }
      setSessionId(null);
    }
    setMessages([]);
    setInput("");
    if (!isGlobalMode) initPaperSession();
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="chatbot-container">

      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            <span className="chat-empty-icon">💬</span>
            <p>
              {isGlobalMode
                ? "Ask anything — I'll search across all papers."
                : "Ask anything about this paper."}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${msg.role}`}>
            <span className="chat-bubble__label">
              {msg.role === "user" ? "You" : msg.role === "error" ? "Error" : "Assistant"}
            </span>
            <p className="chat-bubble__text">{msg.content}</p>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--loading">
            <span className="chat-bubble__label">Assistant</span>
            <span className="chat-typing">
              <span /><span /><span />
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={
            isGlobalMode
              ? "Ask about any paper in the database… (Enter to send)"
              : "Ask a question about this paper… (Enter to send)"
          }
          rows={1}
          disabled={loading}
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          aria-label="Send message"
        >
          {loading ? "…" : "Send"}
        </button>
      </div>

      {messages.length > 0 && (
        <button className="chat-reset-btn" onClick={resetChat}>
          Clear conversation
        </button>
      )}
    </div>
  );
}
