import { useEffect, useRef, useState } from "react";
import { getChatMessages, clearChatMessages, askQuestion } from "../api/datasets";

const EXAMPLE_QUESTIONS = [
  "Which products generated the highest revenue?",
  "Which region is underperforming?",
  "Which customers contribute the most revenue?",
  "What is the expected revenue next month?",
  "Why did sales decrease?",
];

export default function AskTab({ datasetId }) {
  const [messages, setMessages] = useState(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    getChatMessages(datasetId)
      .then(setMessages)
      .catch(() => setMessages([]));
  }, [datasetId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const send = async (question) => {
    const q = (question ?? input).trim();
    if (!q || sending) return;
    setInput("");
    setError("");
    setSending(true);

    // optimistic append of the user's message
    setMessages((prev) => [...(prev || []), { id: `temp-${Date.now()}`, role: "user", content: q }]);

    try {
      const res = await askQuestion(datasetId, q);
      setMessages((prev) => {
        const withoutTemp = (prev || []).filter((m) => !String(m.id).startsWith("temp-"));
        return [...withoutTemp, res.user_message, res.assistant_message];
      });
    } catch (err) {
      setMessages((prev) => (prev || []).filter((m) => !String(m.id).startsWith("temp-")));
      setError(err.response?.data?.errors?.[0] || "Ask INSIGHT IQ couldn't answer that. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleClear = async () => {
    if (!confirm("Clear this conversation? This cannot be undone.")) return;
    await clearChatMessages(datasetId);
    setMessages([]);
  };

  const onSubmit = (e) => {
    e.preventDefault();
    send();
  };

  if (messages === null) {
    return <p className="text-ink-muted text-sm">Loading conversation…</p>;
  }

  return (
    <div className="flex flex-col h-[70vh] max-h-[720px] rounded-xl border border-border bg-surface overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <p className="text-sm text-ink-muted">
          Ask INSIGHT IQ answers using this dataset's computed metrics, insights, and predictive
          results — not the raw file alone.
        </p>
        {messages.length > 0 && (
          <button onClick={handleClear} className="text-xs text-ink-muted hover:text-danger whitespace-nowrap ml-3">
            Clear conversation
          </button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <p className="text-ink font-medium mb-2">Ask something about this dataset</p>
            <p className="text-ink-muted text-sm mb-5 max-w-sm">
              Try one of these, or type your own question below.
            </p>
            <div className="flex flex-col gap-2 w-full max-w-sm">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-sm text-left rounded-lg border border-border px-3 py-2 text-ink-muted hover:text-ink hover:border-signal/40 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <ChatBubble key={m.id} role={m.role} content={m.content} />
        ))}

        {sending && <ChatBubble role="assistant" content="…" pending />}
      </div>

      {error && <p className="px-4 pb-1 text-danger text-xs">{error}</p>}

      <form onSubmit={onSubmit} className="border-t border-border p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about revenue, products, customers, trends…"
          disabled={sending}
          className="flex-1 rounded-lg bg-surface-raised border border-border px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted/60 outline-none focus:border-signal disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-lg bg-signal text-[#06110d] font-medium px-4 py-2.5 text-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function ChatBubble({ role, content, pending }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-signal/15 border border-signal/25 text-ink"
            : "bg-surface-raised border border-border text-ink"
        }`}
      >
        {pending ? <TypingDots /> : content}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1 items-center py-1">
      <span className="w-1.5 h-1.5 rounded-full bg-ink-muted/60 animate-bounce [animation-delay:-0.3s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-ink-muted/60 animate-bounce [animation-delay:-0.15s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-ink-muted/60 animate-bounce" />
    </span>
  );
}
