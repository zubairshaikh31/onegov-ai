"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Users, Search, Shield, CheckCircle2, XCircle, MoreHorizontal } from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { toast } from "sonner";

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users-list", search, page],
    queryFn: () => governmentApi.getAdminUsers({ q: search || undefined, page, page_size: 20 }),
  });

  const toggleStatusMutation = useMutation({
    mutationFn: (userId: string) => governmentApi.toggleUserStatus(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users-list"] });
      toast.success("User account status updated.");
    },
    onError: () => toast.error("Failed to update user status"),
  });

  const users = data?.data?.items || [];
  const total = data?.data?.total || 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">User Management</h1>
        <p className="text-sm text-muted-foreground">
          View registered citizens, administrator accounts, and manage system access ({total} total).
        </p>
      </div>

      <div className="flex items-center gap-3 border border-border rounded-xl px-4 py-2.5 bg-card max-w-md">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by citizen name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="bg-transparent border-none text-sm outline-none w-full"
        />
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/50 border-b border-border text-muted-foreground font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-4">Citizen Name</th>
                <th className="p-4">Email</th>
                <th className="p-4">Roles</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    Loading users directory...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map((u: any) => (
                  <tr key={u.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-4 font-semibold text-foreground flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                        {u.full_name?.charAt(0) || "U"}
                      </div>
                      <div>{u.full_name}</div>
                    </td>
                    <td className="p-4 text-muted-foreground font-mono">{u.email}</td>
                    <td className="p-4">
                      <div className="flex gap-1">
                        {u.roles?.map((r: string) => (
                          <span
                            key={r}
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              r === "admin" ? "bg-amber-500/10 text-amber-500" : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {r}
                          </span>
                        )) || <span className="text-muted-foreground">Citizen</span>}
                      </div>
                    </td>
                    <td className="p-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="h-3 w-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-destructive font-medium">
                          <XCircle className="h-3 w-3" /> Suspended
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => toggleStatusMutation.mutate(u.id)}
                        className="px-3 py-1 rounded-lg border border-border text-[11px] font-medium hover:bg-muted"
                      >
                        {u.is_active ? "Suspend" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
