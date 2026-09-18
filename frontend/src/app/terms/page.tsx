import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-10 px-6">
        <div className="max-w-4xl mx-auto">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground mb-4 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Home
          </Link>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
            Terms of Service
          </h1>
          <p className="text-xs text-muted-foreground">Last updated: August 2026</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8 text-sm leading-relaxed text-foreground/90">
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">1. Non-Governmental Entity Disclaimer</h2>
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-900 dark:text-amber-300 text-xs sm:text-sm">
            <strong>Disclaimer:</strong> OneGov AI is an independent digital civic assistant. We are not officially affiliated with, endorsed by, or representing any Ministry, Department, or statutory agency of the Government of India or State Governments.
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">2. Permitted Use</h2>
          <p>
            You agree to use OneGov AI solely for lawful informational purposes. You may not attempt to reverse engineer, disrupt, overload, or execute malicious automated scripts against our endpoints.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">3. Accuracy & Verification</h2>
          <p>
            While we continuously synchronize and verify data against official portals, government rules and fees are subject to periodic changes by relevant ministries. Users are advised to review the final details on official portals linked on each service page.
          </p>
        </section>
      </div>
    </div>
  );
}
