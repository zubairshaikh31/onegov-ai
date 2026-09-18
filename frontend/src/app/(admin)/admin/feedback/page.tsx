"use client";

import { useQuery } from "@tanstack/react-query";
import { Mail, Clock, CheckCircle2, User, Phone } from "lucide-react";
import { governmentApi } from "@/lib/api/government";

export default function AdminFeedbackPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-feedback-list"],
    queryFn: () => governmentApi.getAdminFeedback(),
  });

  const items = data?.data?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Citizen Inquiries & Grievances</h1>
        <p className="text-sm text-muted-foreground">
          Submissions received via public Contact and Feedback forms.
        </p>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 rounded-2xl bg-muted/40 animate-pulse border border-border" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-card border border-border text-muted-foreground">
            <Mail className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
            <p className="text-sm font-semibold">No citizen inquiries yet.</p>
          </div>
        ) : (
          items.map((m: any) => (
            <div key={m.id} className="p-6 rounded-2xl bg-card border border-border space-y-3 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-foreground">{m.subject}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-500/10 text-blue-600 dark:text-blue-400">
                    {m.status || "New"}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground font-mono">
                  {new Date(m.created_at).toLocaleString()}
                </span>
              </div>

              <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
                {m.message}
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-2">
                <span className="flex items-center gap-1.5 font-medium text-foreground">
                  <User className="h-3.5 w-3.5 text-primary" /> {m.name}
                </span>
                <span className="flex items-center gap-1.5 font-mono">
                  <Mail className="h-3.5 w-3.5" /> {m.email}
                </span>
                {m.phone && (
                  <span className="flex items-center gap-1.5 font-mono">
                    <Phone className="h-3.5 w-3.5" /> {m.phone}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
