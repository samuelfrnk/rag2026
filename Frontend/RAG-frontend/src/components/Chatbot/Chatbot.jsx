import { useState, useRef, useEffect } from "react";
import { chatWithPaper, clearChatSession } from "../../services/api"; // ← adjust path if needed
import "./Chatbot.css";

// ─── PaperChatbot ─────────────────────────────────────────────────────────────
//
// Props:
//   paper  — (optional) a specific paper object to pin the chat to.
//             When omitted, the backend performs a free-form RAG search
//             across the entire paper database (global Q&A mode).
//
// Session lifecycle:
//   • sessionId starts null → first POST creates a new server-side session
//   • Backend returns session_id → stored and sent on every subsequent turn
//   • On unmount the session is DELETE'd from the server to avoid memory leaks

export default function PaperChatbot({ paper }) {
  const isGlobalMode = !paper; // true when used on the home page

  // Each message: { role: "user" | "assistant" | "error", content: string }
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const bottomRef    = useRef(null);
  const textareaRef  = useRef(null);
  const sessionIdRef = useRef(null); // ref so the cleanup effect always reads the latest value

  // ── Auto-scroll whenever messages or loading state change ─────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Keep ref in sync with state (closures in cleanup won't stale-capture) ─
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // ── Delete session from server when user navigates away ───────────────────
  useEffect(() => {
    return () => {
      if (sessionIdRef.current) {
        clearChatSession(sessionIdRef.current).catch(() => {});
      }
    };
  }, []);

  // ── Auto-resize textarea up to 120 px ────────────────────────────────────
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

    // Reset input immediately for responsiveness
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    // Optimistically show the user's bubble
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setLoading(true);

    try {
      // Only include paperId when a specific paper is provided.
      // In global mode, the backend will search the full vector index.
      const payload = {
        message:   userText,
        sessionId,
        ...(paper ? { paperId: paper.id } : {}),
      };

      const data = await chatWithPaper(payload);

      if (!sessionId) setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
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

  // ── Wipe local state and delete server session ────────────────────────────
  const resetChat = () => {
    if (sessionId) {
      clearChatSession(sessionId).catch(() => {});
      setSessionId(null);
    }
    setMessages([]);
    setInput("");
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="chatbot-container">

      {/* Message list */}
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

      {/* Input row */}
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

      {/* Clear button — only shown once conversation has started */}
      {messages.length > 0 && (
        <button className="chat-reset-btn" onClick={resetChat}>
          Clear conversation
        </button>
      )}
    </div>
  );
}
