"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

const BULLETS = [
  "Access 1000+ central and state services",
  "AI-guided step-by-step applications",
  "Scheme eligibility in under 60 seconds",
  "Available in English, Hindi & Marathi",
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[52%] xl:w-[55%] relative flex-col justify-between p-12 overflow-hidden bg-card border-r border-border">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -left-32 h-80 w-80 rounded-full bg-blue-600/15 blur-3xl" />
          <div className="absolute -bottom-32 -right-32 h-80 w-80 rounded-full bg-purple-600/15 blur-3xl" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.08),transparent)]" />
          <div className="absolute inset-0 dot-grid opacity-40" />
        </div>

        <div className="relative">
          <Link href="/" className="flex items-center gap-2.5 w-fit">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-lg">🇮🇳</div>
            <span className="font-semibold text-foreground">OneGov AI</span>
          </Link>
        </div>

        <div className="relative space-y-8">
          <div>
            <div className="mb-4 h-px w-10 bg-gradient-to-r from-primary to-purple-500 rounded-full" />
            <h1 className="text-4xl xl:text-5xl font-bold text-foreground leading-tight mb-4">
              Your government,<br />
              <span className="gradient-text">simplified.</span>
            </h1>
            <p className="text-muted-foreground text-lg leading-relaxed max-w-sm">
              The intelligent layer between citizens and India&apos;s government services.
            </p>
          </div>
          <ul className="space-y-3">
            {BULLETS.map((b) => (
              <li key={b} className="flex items-center gap-3 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                {b}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative border-t border-border pt-6">
          <p className="text-xs text-muted-foreground">
            Not affiliated with the Government of India
          </p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex flex-1 flex-col bg-background">
        <div className="lg:hidden flex items-center justify-between border-b border-border px-5 py-3">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg">🇮🇳</span>
            <span className="font-semibold text-sm">OneGov AI</span>
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-center p-6 sm:p-10">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-md"
          >
            {children}
          </motion.div>
        </div>

        <div className="border-t border-border px-6 py-4 text-center text-xs text-muted-foreground">
          <Link href="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
          {" · "}
          <Link href="/terms" className="hover:text-foreground transition-colors">Terms</Link>
          {" · "}
          <span>© {new Date().getFullYear()} OneGov AI</span>
        </div>
      </div>
    </div>
  );
}
