"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Info, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["user-notifications"],
    queryFn: () => governmentApi.getNotifications(),
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => governmentApi.markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["user-notifications"] }),
  });

  const readAllMutation = useMutation({
    mutationFn: () => governmentApi.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-notifications"] }),
      toast.success("All notifications marked as read");
    },
  });

  const notifs = data?.data || [];
  const unread = notifs.filter((n) => !n.is_read).length;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Notifications</h1>
          <p className="text-sm text-muted-foreground mt-1">{unread} unread notifications</p>
        </div>
        {unread > 0 && (
          <button
            onClick={() => readAllMutation.mutate()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border text-xs font-semibold hover:bg-muted text-foreground transition-colors"
          >
            <CheckCheck className="h-4 w-4" />
            Mark all as read
          </button>
        )}
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-20 rounded-2xl bg-muted/40 animate-pulse border border-border" />
            ))}
          </div>
        ) : notifs.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-card border border-border">
            <Bell className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
            <p className="text-sm font-bold text-foreground">No notifications yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              You will receive updates on scheme eligibility and tracked service announcements here.
            </p>
          </div>
        ) : (
          notifs.map((n) => (
            <div
              key={n.id}
              onClick={() => !n.is_read && readMutation.mutate(n.id)}
              className={cn(
                "rounded-2xl border p-4 transition-colors cursor-pointer shadow-sm",
                !n.is_read
                  ? "bg-card border-primary/30"
                  : "bg-muted/20 border-border/60"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary mt-0.5">
                  <Bell className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className={cn("text-sm font-bold", n.is_read ? "text-muted-foreground" : "text-foreground")}>
                      {n.title}
                    </p>
                    {!n.is_read && <span className="h-2 w-2 flex-shrink-0 rounded-full bg-primary" />}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{n.message}</p>
                  <p className="text-[10px] text-muted-foreground/60 mt-2 font-mono">
                    {new Date(n.created_at).toLocaleString()}
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
