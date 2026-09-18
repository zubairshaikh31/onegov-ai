import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";

export default function PrivacyPolicyPage() {
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
            Privacy Policy
          </h1>
          <p className="text-xs text-muted-foreground">Last updated: August 2026</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8 text-sm leading-relaxed text-foreground/90">
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">1. Introduction</h2>
          <p>
            OneGov AI (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard information when you visit and use our digital civic assistance platform.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">2. Information We Do NOT Collect</h2>
          <p className="p-4 rounded-xl bg-muted/40 border border-border">
            <strong>Important:</strong> We never collect, process, or store full 12-digit Aadhaar numbers, biometric data, PAN cards, or banking credentials. We are an informational guide and search portal; you submit official documents solely on official Government of India websites.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">3. Information We Collect</h2>
          <ul className="list-disc pl-5 space-y-1.5 text-muted-foreground">
            <li><strong>Account Details:</strong> Name, email address, phone number (for OTP verification), and preferred language/state.</li>
            <li><strong>Search & Interaction Logs:</strong> Anonymous search queries and AI chat history to improve conversational accuracy.</li>
            <li><strong>Technical Analytics:</strong> Browser type, device category, and IP address for security and rate-limiting.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">4. How We Use Information</h2>
          <p>
            Your information is used strictly to provide personalized recommendations for state schemes, retain your saved bookmarks, authenticate your sessions, and secure our infrastructure.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">5. Contact</h2>
          <p>
            For privacy inquiries, contact our Data Protection Officer at <a href="mailto:privacy@onegov.ai" className="text-primary hover:underline">privacy@onegov.ai</a>.
          </p>
        </section>
      </div>
    </div>
  );
}
