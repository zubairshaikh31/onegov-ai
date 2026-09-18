"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Building2, FileText, MessageSquare, Search,
  BookMarked, Bell, User, Settings, LogOut, Menu, X, ChevronRight,
  Sparkles, Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const NAV = [
  { href: "/dashboard",      label: "Dashboard",     icon: LayoutDashboard },
  { href: "/services",       label: "Services",      icon: Building2 },
  { href: "/schemes",        label: "Schemes",       icon: FileText },
  { href: "/ai-chat",        label: "AI Assistant",  icon: MessageSquare, badge: "AI" },
  { href: "/search",         label: "Search",        icon: Search },
  { href: "/bookmarks",      label: "Bookmarks",     icon: BookMarked },
  { href: "/notifications",  label: "Notifications", icon: Bell },
  { href: "/profile",        label: "Profile",       icon: User },
  { href: "/settings",       label: "Settings",      icon: Settings },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout, isAdmin } = useAuth();

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-base">🇮🇳</div>
        <div>
          <p className="text-sm font-semibold text-foreground">OneGov AI</p>
          <p className="text-xs text-muted-foreground">Government Services</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
        {NAV.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
                active
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}>
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {badge && (
                <span className="rounded-md bg-primary/20 px-1.5 py-0.5 text-[10px] font-semibold text-primary">{badge}</span>
              )}
              {active && <ChevronRight className="h-3 w-3 opacity-50" />}
            </Link>
          );
        })}

        {isAdmin && (
          <Link href="/admin" onClick={onNavigate}
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-amber-500 hover:bg-amber-500/10 transition-all mt-2">
            <Shield className="h-4 w-4" />
            Admin Panel
          </Link>
        )}
      </nav>

      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 border border-primary/20 text-sm font-bold text-primary">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-foreground">{user?.full_name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </div>
        <button onClick={logout}
          className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted-foreground transition-all hover:text-destructive hover:bg-destructive/5">
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 xl:w-72 flex-col border-r border-border bg-card fixed inset-y-0 left-0 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setOpen(false)} className="fixed inset-0 bg-black/60 z-40 lg:hidden" />
            <motion.aside
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-50 w-72 bg-card border-r border-border lg:hidden">
              <button onClick={() => setOpen(false)}
                className="absolute right-3 top-3 rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent">
                <X className="h-5 w-5" />
              </button>
              <SidebarContent onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex-1 lg:pl-64 xl:pl-72 flex flex-col min-h-screen">
        {/* Mobile topbar */}
        <header className="lg:hidden sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card/80 backdrop-blur-xl px-4">
          <button onClick={() => setOpen(true)} className="rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent">
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-base">🇮🇳</span>
            <span className="font-semibold text-sm">OneGov AI</span>
          </div>
          <Link href="/notifications" className="rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent">
            <Bell className="h-5 w-5" />
          </Link>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
