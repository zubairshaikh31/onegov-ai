"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, User, Clock } from "lucide-react";
import { governmentApi } from "@/lib/api/government";

export default function AdminAiLogsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-ai-logs"],
    queryFn: () => governmentApi.getAdminAiLogs({ page_size: 30 }),
  });

  const logs = data?.data?.items || [];
  const total = data?.data?.total || 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Conversation Logs</h1>
        <p className="text-sm text-muted-foreground">
          Audit citizen questions and AI responses for hallucination monitoring and RAG retrieval verification ({total} total).
        </p>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-32 rounded-2xl bg-muted/40 animate-pulse border border-border" />
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-card border border-border text-muted-foreground">
            <Bot className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
            <p className="text-sm font-semibold">No AI conversation records yet.</p>
          </div>
        ) : (
          logs.map((log: any) => (
            <div key={log.id} className="p-5 rounded-2xl bg-card border border-border space-y-3 shadow-sm">
              <div className="flex items-center justify-between text-xs text-muted-foreground border-b border-border/40 pb-2">
                <span className="font-mono">Session ID: {log.session_id || log.id}</span>
                <span>{new Date(log.created_at).toLocaleString()}</span>
              </div>

              {/* User prompt */}
              <div className="flex items-start gap-3 p-3 rounded-xl bg-muted/30">
                <div className="p-1.5 rounded-lg bg-primary/10 text-primary mt-0.5">
                  <User className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1">
                  <p className="text-[11px] font-bold text-muted-foreground uppercase">Citizen Query</p>
                  <p className="text-xs text-foreground font-medium mt-0.5">{log.message}</p>
                </div>
              </div>

              {/* Assistant response */}
              <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-500/5 border border-blue-500/10">
                <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 mt-0.5">
                  <Bot className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1">
                  <p className="text-[11px] font-bold text-blue-600 dark:text-blue-400 uppercase">AI Answer</p>
                  <p className="text-xs text-foreground/90 leading-relaxed mt-0.5 whitespace-pre-line">
                    {log.response}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
