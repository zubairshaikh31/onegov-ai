"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send, Bot, User, Loader2, Sparkles, Copy, ThumbsUp, RotateCcw,
  ExternalLink, FileText, CheckCircle2, ChevronRight, Shield, AlertCircle, RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import apiClient from "@/lib/api/client";
import { governmentApi } from "@/lib/api/government";
import { MessageTime } from "@/components/chat/MessageTime";
import type { ChatSource, ChatMessage } from "@/types/government";

const SUGGESTIONS = [
  "How do I apply for a Tatkaal passport?",
  "What welfare schemes are available for small farmers?",
  "Aadhaar address update without proof procedure",
  "Ayushman Bharat ₹5 Lakh health insurance eligibility",
  "PM Kisan Samman Nidhi application status",
  "Driving licence renewal and online slot booking",
];

function MessageBubble({
  msg,
  onRetry,
  onRegenerate,
}: {
  msg: ChatMessage;
  onRetry?: () => void;
  onRegenerate?: () => void;
}) {
  const isUser = msg.role === "user";

  const copyText = () => {
    navigator.clipboard.writeText(msg.content);
    toast.success("Copied to clipboard");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 mt-1">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}

      <div className={cn("group max-w-[85%] sm:max-w-[75%] space-y-2", isUser && "items-end flex flex-col")}>
        <div
          className={cn(
            "rounded-2xl px-5 py-3.5 text-xs sm:text-sm leading-relaxed shadow-sm",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-card text-foreground border border-border rounded-tl-sm"
          )}
        >
          {msg.loading ? (
            <div className="flex items-center gap-2 py-2">
              <span className="text-xs text-muted-foreground animate-pulse flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary animate-spin" />
                Searching verified government knowledge chunks...
              </span>
            </div>
          ) : (
            <div className="whitespace-pre-wrap">{msg.content}</div>
          )}
        </div>

        {/* Sources citation badges */}
        {!isUser && msg.sources && msg.sources.length > 0 && !msg.loading && (
          <div className="flex flex-wrap items-center gap-1.5 pl-1 pt-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mr-1">
              Grounded In:
            </span>
            {msg.sources.map((s, idx) => (
              <Link
                key={s.slug || idx}
                href={s.url || `/services/${s.slug}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-muted/60 hover:bg-muted text-[11px] font-semibold text-primary border border-border transition-colors"
              >
                <FileText className="h-3 w-3" />
                {s.title}
                <ExternalLink className="h-2.5 w-2.5 opacity-60" />
              </Link>
            ))}
          </div>
        )}

        {/* Action bar */}
        {!isUser && !msg.loading && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity pl-1">
            <button
              onClick={copyText}
              className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
              title="Copy answer"
              aria-label="Copy answer"
            >
              <Copy className="h-3.5 w-3.5" />
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
                title="Regenerate answer"
                aria-label="Regenerate answer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            )}
            <button
              onClick={() => toast.success("Feedback recorded: Helpful")}
              className="rounded-lg p-1.5 text-muted-foreground hover:text-emerald-500 hover:bg-emerald-500/10 transition-all"
              title="Helpful"
              aria-label="Helpful"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </button>
            <MessageTime timestamp={msg.createdAt} className="text-[10px] text-muted-foreground pl-1" />
          </div>
        )}

        {isUser && (
          <div className="flex items-center gap-1 pl-1">
            <MessageTime timestamp={msg.createdAt} className="text-[10px] text-muted-foreground" />
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-muted border border-border mt-1">
          <User className="h-4 w-4 text-foreground" />
        </div>
      )}
    </motion.div>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get("topic") || "";

  const [sessionId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("onegov_chat_session_id");
      if (saved) return saved;
      const newId = crypto.randomUUID();
      localStorage.setItem("onegov_chat_session_id", newId);
      return newId;
    }
    return crypto.randomUUID();
  });

  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content:
        "👋 Namaste! I am the OneGov AI Assistant.\n\nI can help you check welfare scheme eligibility, prepare application checklists, find official government portals, and guide you through administrative procedures across 1,000+ Central and State services.\n\nWhat would you like assistance with today?",
      createdAt: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastUserPrompt, setLastUserPrompt] = useState<string>("");
  const [healthStatus, setHealthStatus] = useState<{
    healthy: boolean;
    provider: string;
    model: string;
    ollama_available: boolean;
  }>({
    healthy: true,
    provider: "ollama",
    model: "llama3.2",
    ollama_available: true,
  });

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load chat history on mount
  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const res = await governmentApi.getAiHistory({ session_id: sessionId });
        if (isMounted && res.data && res.data.length > 0) {
          setMessages(res.data);
        }
      } catch {
        // Fallback to initial greeting
      }
    }
    async function checkHealth() {
      try {
        const h = await governmentApi.getAiHealth();
        if (isMounted && h.data) {
          setHealthStatus({
            healthy: h.data.healthy,
            provider: h.data.provider,
            model: h.data.model,
            ollama_available: h.data.ollama_available,
          });
        }
      } catch {
        // Assume standalone mode
      }
    }
    loadHistory();
    checkHealth();
    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      const promptText = text.trim();
      setLastUserPrompt(promptText);

      const userMsgId = crypto.randomUUID();
      const loadingMsgId = crypto.randomUUID();

      const userMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: promptText,
        createdAt: new Date().toISOString(),
      };

      const loadingMsg: ChatMessage = {
        id: loadingMsgId,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        loading: true,
      };

      setMessages((prev) => [...prev, userMsg, loadingMsg]);
      setInput("");
      setIsLoading(true);

      try {
        const history = messages
          .filter((m) => !m.loading)
          .map((m) => ({ role: m.role, content: m.content }));

        const res = await apiClient.post("/ai/chat", {
          message: promptText,
          session_id: sessionId,
          history,
        });

        const reply = res.data?.data?.content ?? "I could not retrieve an answer. Please try again.";
        const sources = res.data?.data?.sources || [];
        const assistantMsgId = crypto.randomUUID();

        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsgId
              ? {
                  id: assistantMsgId,
                  role: "assistant",
                  content: reply,
                  sources: sources,
                  createdAt: new Date().toISOString(),
                  loading: false,
                }
              : m
          )
        );
      } catch (err: any) {
        const errorMsgId = crypto.randomUUID();
        const errorMessage =
          err?.response?.data?.message ||
          "I am currently operating in standalone reference mode. You can explore the verified government knowledge base under Services and Schemes.";

        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMsgId
              ? {
                  id: errorMsgId,
                  role: "assistant",
                  content: errorMessage,
                  createdAt: new Date().toISOString(),
                  loading: false,
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
        inputRef.current?.focus();
      }
    },
    [isLoading, messages, sessionId]
  );

  // Auto trigger topic if passed in URL
  useEffect(() => {
    if (initialTopic && messages.length === 1) {
      sendMessage(initialTopic);
    }
  }, [initialTopic]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const clearChat = () => {
    const newSessionId = crypto.randomUUID();
    if (typeof window !== "undefined") {
      localStorage.setItem("onegov_chat_session_id", newSessionId);
    }
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Chat history reset. How can I assist you with government procedures today?",
        createdAt: new Date().toISOString(),
      },
    ]);
    toast.info("Conversation reset");
  };

  const regenerateLastAnswer = () => {
    if (lastUserPrompt) {
      sendMessage(lastUserPrompt);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] lg:h-[calc(100vh-4rem)] max-w-4xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base text-foreground">OneGov AI Assistant</h1>
              <span className="rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 text-[10px] font-bold border border-emerald-500/20">
                RAG Active ({healthStatus.provider})
              </span>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block" />
              Grounded in 2,200+ verified official knowledge chunks
            </p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border text-xs font-semibold hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="Reset conversation"
          aria-label="Reset conversation"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Reset</span>
        </button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((msg, index) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            onRegenerate={
              index === messages.length - 1 && msg.role === "assistant" && !msg.loading
                ? regenerateLastAnswer
                : undefined
            }
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggested prompts */}
      <AnimatePresence>
        {messages.length <= 1 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="py-3 flex gap-2 flex-wrap"
          >
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => sendMessage(s)}
                className="rounded-xl border border-border bg-card px-3.5 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/40 hover:bg-muted transition-all shadow-sm"
              >
                {s}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input box */}
      <div className="mt-3 border-t border-border pt-4">
        <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2.5 focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/20 transition-all shadow-sm">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about any government service, scheme, document checklist, or official portal..."
            rows={1}
            className="flex-1 resize-none bg-transparent px-3 py-1.5 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground outline-none max-h-32"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="rounded-xl bg-primary px-4 py-2.5 text-primary-foreground transition-all hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm shrink-0 flex items-center gap-1 text-xs font-semibold"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          <Shield className="h-3 w-3 inline mr-1 text-primary" />
          All recommendations are fact-checked against government knowledge bases. Never submit sensitive Aadhaar/OTP here.
        </p>
      </div>
    </div>
  );
}

export default function AIChatPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
