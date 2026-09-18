"use client";

import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

const PWD_RULES = [
  { label: "8+ chars",          test: (p: string) => p.length >= 8 },
  { label: "Uppercase (A-Z)",  test: (p: string) => /[A-Z]/.test(p) },
  { label: "Lowercase (a-z)",  test: (p: string) => /[a-z]/.test(p) },
  { label: "Number (0-9)",     test: (p: string) => /[0-9]/.test(p) },
  { label: "Special (@$!%*?&)", test: (p: string) => /[@$!%*?&]/.test(p) },
];

export function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;
  const score = PWD_RULES.filter((r) => r.test(password)).length;
  const colors = ["", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-blue-500", "bg-emerald-500"];
  const labels = ["", "Very Weak", "Weak", "Fair", "Good", "Strong"];

  return (
    <div className="mt-2.5 space-y-2 p-3 rounded-xl bg-accent/40 border border-border/60">
      <div className="flex gap-1.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-all duration-300",
              i <= score ? colors[score] : "bg-muted"
            )}
          />
        ))}
      </div>
      <div className="flex items-center justify-between">
        <p className={cn("text-xs font-semibold", score <= 2 ? "text-red-400" : score <= 3 ? "text-yellow-400" : "text-emerald-400")}>
          {labels[score]} Password
        </p>
        <span className="text-[11px] text-muted-foreground">{score}/5 rules met</span>
      </div>
      <div className="grid grid-cols-2 gap-1.5 pt-1 border-t border-border/40">
        {PWD_RULES.map((r) => {
          const met = r.test(password);
          return (
            <div key={r.label} className={cn("flex items-center gap-1.5 text-xs transition-colors", met ? "text-emerald-500 font-medium" : "text-muted-foreground/60")}>
              {met ? <Check className="h-3 w-3 flex-shrink-0" /> : <X className="h-3 w-3 flex-shrink-0 opacity-40" />}
              <span>{r.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
