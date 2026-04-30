import { useState, useRef, useEffect } from "react";
import { chatWithPaper, clearChatSession } from "../../services/api"; // ← adjust path if needed
import "./Chatbot.css";

// ─── PaperChatbot ─────────────────────────────────────────────────────────────
//
// Props:
//   paper  — the full paper object from route state / localStorage
//
// Session lifecycle:
//   • sessionId starts null → first POST creates a new server-side session
//   • Backend returns session_id → stored and sent on every subsequent turn
//   • On unmount the session is DELETE'd from the server to avoid memory leaks
//
// Paper-specificity:
//   • paper.id is sent as paper_id so the backend fetches that exact document
//     from the vector index instead of doing a free-form semantic search.
//   • Note: paper.id in the current dummy data is the rank integer (1, 2, …).
//     When the real backend is wired up, swap paper.id for whichever field
//     holds the arXiv ID (e.g. "1706.03762" extracted from the DOI, or an
//     entry_id field returned by the API).

export default function PaperChatbot({ paper }) {
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
      const data = await chatWithPaper({
        message:   userText,
        sessionId,          // null on first turn → server creates a fresh session
        paperId:   paper.id // tells backend to retrieve this specific paper
      });

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
            {/*<span className="chat-empty-icon">💬</span>*/}
            { /* <p>Ask anything about this paper.</p> */}
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
          placeholder="Ask a question… (Enter to send, Shift+Enter for new line)"
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
