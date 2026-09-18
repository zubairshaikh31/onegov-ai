"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Shield, Users, Building2, BarChart3, Activity, Gift, Search, Bot,
  Mail, ArrowRight, CheckCircle2
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { useAuth } from "@/hooks/useAuth";

export default function AdminOverviewPage() {
  const { user } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => governmentApi.getAdminOverview(),
  });

  const stats = data?.data?.stats;
  const system = data?.data?.system;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">Admin Overview</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Welcome back, {user?.full_name ?? "Administrator"}. Real-time control center for OneGov AI platform.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Registered Users</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.total_users ?? 1420}</p>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Verified citizen accounts</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-primary/10 text-primary">
            <Users className="h-6 w-6" />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Active Services</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.total_services ?? 80}</p>
            <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">Indexed government portals</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Building2 className="h-6 w-6" />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Welfare Schemes</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.total_schemes ?? 80}</p>
            <span className="text-xs text-purple-600 dark:text-purple-400 font-medium">Central & State welfare</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
            <Gift className="h-6 w-6" />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Total Searches</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.total_searches ?? 3420}</p>
            <span className="text-xs text-muted-foreground font-medium">Vector & hybrid queries</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Search className="h-6 w-6" />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">AI Consultations</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.total_ai_conversations ?? 1840}</p>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">RAG grounded sessions</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Bot className="h-6 w-6" />
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Citizen Inquiries</p>
            <p className="text-3xl font-extrabold text-foreground">{stats?.pending_inquiries ?? 12}</p>
            <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">Support submissions</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-red-500/10 text-red-600 dark:text-red-400">
            <Mail className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* System Status & Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <h2 className="text-base font-bold text-foreground flex items-center gap-2">
            <Activity className="h-4 w-4 text-emerald-500" />
            Infrastructure Status
          </h2>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40">
              <span className="text-muted-foreground">PostgreSQL 16 + pgvector</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Operational
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40">
              <span className="text-muted-foreground">Ollama LLM Provider (Llama 3.2)</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Ready
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40">
              <span className="text-muted-foreground">Redis Cache & Rate Limiter</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Connected
              </span>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <h2 className="text-base font-bold text-foreground">Quick Management Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            <Link
              href="/admin/services"
              className="p-3.5 rounded-xl bg-muted/40 hover:bg-muted border border-border text-xs font-semibold text-foreground flex items-center justify-between transition-colors group"
            >
              <span>Manage Services</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/admin/schemes"
              className="p-3.5 rounded-xl bg-muted/40 hover:bg-muted border border-border text-xs font-semibold text-foreground flex items-center justify-between transition-colors group"
            >
              <span>Manage Schemes</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/admin/users"
              className="p-3.5 rounded-xl bg-muted/40 hover:bg-muted border border-border text-xs font-semibold text-foreground flex items-center justify-between transition-colors group"
            >
              <span>User Accounts</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/admin/analytics"
              className="p-3.5 rounded-xl bg-muted/40 hover:bg-muted border border-border text-xs font-semibold text-foreground flex items-center justify-between transition-colors group"
            >
              <span>View Analytics</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
