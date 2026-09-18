"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home, Bot } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application Error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center p-4 mb-6 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive">
          <AlertTriangle className="h-10 w-10" />
        </div>

        <p className="text-sm font-semibold tracking-wider uppercase text-destructive mb-2">500 Server Error</p>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-3">Something went wrong</h1>
        <p className="text-muted-foreground text-sm mb-8 leading-relaxed">
          An unexpected error occurred while communicating with government data services. Please try refreshing.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-muted hover:bg-muted/80 text-foreground font-medium border border-border transition-colors"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
          <Link
            href="/ai-chat"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 font-medium border border-blue-500/20 transition-colors"
          >
            <Bot className="h-4 w-4" />
            Ask Assistant
          </Link>
        </div>
      </div>
    </div>
  );
}
