"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

interface AuthCardProps {
  title: string;
  subtitle: React.ReactNode;
  children: React.ReactNode;
  icon?: React.ReactNode;
}


export function AuthCard({ title, subtitle, children, icon }: AuthCardProps) {
  return (
    <div className="relative w-full max-w-md mx-auto">
      {/* Background glowing blobs */}
      <div className="absolute -top-12 -left-12 h-64 w-64 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -right-12 h-64 w-64 rounded-full bg-blue-600/15 blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="relative z-10 rounded-3xl border border-border/80 bg-card/80 backdrop-blur-xl p-6 sm:p-8 shadow-2xl shadow-black/10"
      >
        <div className="text-center space-y-2 mb-6">
          <div className="inline-flex items-center justify-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-semibold text-primary mb-2">
            <span className="text-sm">🇮🇳</span>
            <span>OneGov AI</span>
            <Sparkles className="h-3 w-3" />
          </div>

          {icon && <div className="flex justify-center mb-2">{icon}</div>}

          <h1 className="text-2xl font-bold tracking-tight text-foreground">{title}</h1>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>

        {children}
      </motion.div>
    </div>
  );
}
