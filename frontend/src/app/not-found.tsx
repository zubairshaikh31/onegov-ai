"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Home, Search, Bot, ArrowRight, ShieldAlert, Sparkles } from "lucide-react";

export default function NotFound() {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-background px-6 overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 right-10 w-[400px] h-[400px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-xl text-center">
        {/* Government emblem / illustration container */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center justify-center p-4 mb-6 rounded-2xl bg-muted/60 border border-border shadow-xl backdrop-blur-md"
        >
          <div className="relative flex items-center justify-center w-20 h-20 rounded-xl bg-gradient-to-br from-primary/20 via-blue-500/10 to-transparent border border-primary/30">
            <span className="text-4xl">🏛️</span>
            <span className="absolute -top-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-amber-500"></span>
            </span>
          </div>
        </motion.div>

        {/* Large 404 text */}
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="text-7xl sm:text-9xl font-extrabold tracking-tight bg-gradient-to-b from-foreground via-foreground/80 to-muted-foreground/30 bg-clip-text text-transparent select-none mb-2"
        >
          404
        </motion.h1>

        {/* Heading and description */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-3">
            The service you&apos;re looking for doesn&apos;t exist.
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base mb-8 max-w-md mx-auto leading-relaxed">
            The requested government portal, scheme, or page may have been relocated or updated under our digital directory.
          </p>
        </motion.div>

        {/* Action shortcuts */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="flex flex-col sm:flex-row gap-3 justify-center items-center"
        >
          <Link
            href="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Home className="h-4 w-4" />
            Back Home
          </Link>
          <Link
            href="/services"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-muted hover:bg-muted/80 text-foreground font-medium border border-border transition-colors"
          >
            <Search className="h-4 w-4 text-muted-foreground" />
            Search Services
          </Link>
          <Link
            href="/ai-chat"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 font-medium border border-blue-500/20 transition-colors"
          >
            <Bot className="h-4 w-4" />
            Ask AI Assistant
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
