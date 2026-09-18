"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  MessageSquare, Search, Building2, Gift, ArrowRight, Bookmark,
  TrendingUp, Zap, Clock, Shield, ArrowUpRight, Sparkles, CheckCircle2
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { governmentApi } from "@/lib/api/government";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.4 } }),
};

const QUICK_ACTIONS = [
  {
    icon: Search,
    label: "Global Search",
    desc: "Search services & schemes instantly",
    href: "/search",
    bg: "bg-blue-500/10 text-blue-500",
  },
  {
    icon: Sparkles,
    label: "AI Consultation",
    desc: "Personalized eligibility & advice",
    href: "/ai-chat",
    bg: "bg-purple-500/10 text-purple-500",
    badge: "RAG AI",
  },
  {
    icon: Building2,
    label: "Government Services",
    desc: "Browse 80+ citizen portals",
    href: "/services",
    bg: "bg-emerald-500/10 text-emerald-500",
  },
  {
    icon: Gift,
    label: "Welfare Schemes",
    desc: "Find financial subsidies & aid",
    href: "/schemes",
    bg: "bg-amber-500/10 text-amber-500",
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.full_name?.split(" ")[0] ?? "Citizen";

  const { data: featuredServices } = useQuery({
    queryKey: ["featured-services"],
    queryFn: () => governmentApi.getFeaturedServices(),
  });

  const { data: bookmarksData } = useQuery({
    queryKey: ["user-bookmarks"],
    queryFn: () => governmentApi.getBookmarks(),
  });

  const services = featuredServices?.data || [];
  const bookmarksCount = (bookmarksData?.data?.services?.length || 0) + (bookmarksData?.data?.schemes?.length || 0);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Welcome Banner */}
      <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
        <div className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-card to-purple-500/10 p-8 shadow-sm">
          <div className="relative z-10">
            <p className="text-xs font-semibold uppercase tracking-wider text-primary mb-1">
              {greeting} 👋
            </p>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground mb-2">
              Welcome back, {firstName}!
            </h1>
            <p className="text-muted-foreground text-sm max-w-md mb-6 leading-relaxed">
              Your intelligent civic command center. Search government services, check welfare eligibility, and get step-by-step guidance.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/ai-chat"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm"
              >
                <Sparkles className="h-4 w-4" />
                Ask AI Assistant
              </Link>
              <Link
                href="/search"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border border-border text-foreground text-xs font-semibold hover:bg-muted transition-colors"
              >
                <Search className="h-4 w-4 text-muted-foreground" />
                Search Directory
              </Link>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
          Quick Navigation
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {QUICK_ACTIONS.map((action, i) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} href={action.href}>
                <div className="group flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-sm">
                  <div className={cn("flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl", action.bg)}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                        {action.label}
                      </p>
                      {action.badge && (
                        <span className="rounded-md bg-primary/10 text-primary px-1.5 py-0.5 text-[10px] font-bold">
                          {action.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{action.desc}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0 transition-transform group-hover:translate-x-1" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Popular Services & Bookmarks Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Live Popular Services */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
              <Building2 className="h-4 w-4 text-primary" />
              Featured Government Services
            </h3>
            <Link href="/services" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {services.slice(0, 4).map((s) => (
              <Link key={s.id} href={`/services/${s.slug}`}>
                <div className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/40 transition-colors group">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm font-bold text-foreground truncate group-hover:text-primary transition-colors">
                      {s.name}
                    </p>
                    <p className="text-[11px] text-muted-foreground truncate">{s.category?.name || "General"}</p>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all ml-2" />
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Bookmarks Summary */}
        <div className="flex flex-col justify-between rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Bookmark className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-foreground">Saved Services & Schemes</h3>
                <p className="text-xs text-muted-foreground">{bookmarksCount} items in your bookmarks</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed mt-2">
              Keep your frequently accessed document checklists and pending welfare applications pinned for instant retrieval.
            </p>
          </div>
          <Link
            href="/bookmarks"
            className="mt-6 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-muted hover:bg-muted/80 text-foreground text-xs font-semibold transition-colors border border-border"
          >
            Manage Bookmarks <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
