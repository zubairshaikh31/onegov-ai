"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles, Shield, Zap, Globe2, Building2, Code2, Database, Cpu,
  CheckCircle2, ArrowRight, Heart, Users, Lock, Award
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Hero Section */}
      <div className="relative border-b border-border bg-gradient-to-b from-muted/50 via-background to-background pt-28 pb-16 px-6 overflow-hidden">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary mb-4">
            <Sparkles className="h-3.5 w-3.5" />
            Next-Generation Civic Technology
          </div>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
            Democratizing Access to Government Services with AI
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            OneGov AI is an intelligent digital gateway engineered to simplify complex bureaucracy, eliminate informational barriers, and empower 1.4 billion citizens with instant, accurate government assistance.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-16 space-y-16">
        {/* Mission & Vision */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 rounded-3xl bg-card border border-border">
            <div className="p-3 rounded-2xl bg-primary/10 text-primary w-fit mb-4">
              <Zap className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold text-foreground mb-3">Our Mission</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              To make every citizen service, welfare scheme, and administrative process in India accessible in seconds through natural language intelligence, clear document checklists, and transparent official procedures.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-card border border-border">
            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400 w-fit mb-4">
              <Globe2 className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold text-foreground mb-3">Our Vision</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              A friction-free digital India where no eligible family misses out on welfare entitlements, healthcare subsidies, or essential civic documents due to lack of awareness or bureaucratic friction.
            </p>
          </div>
        </div>

        {/* Technology Architecture */}
        <div>
          <div className="text-center max-w-2xl mx-auto mb-10">
            <div className="text-xs font-bold uppercase tracking-wider text-primary mb-2">Built for Performance & Scale</div>
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground">Modern Engineering Stack</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
            {[
              {
                icon: Cpu,
                title: "Retrieval Augmented Gen (RAG)",
                desc: "Powered by Ollama Llama 3.2 with strict factual grounding against our verified knowledge base.",
              },
              {
                icon: Database,
                title: "pgvector & PostgreSQL 16",
                desc: "High-dimensional vector similarity search with full ACID transactions and pg_trgm typo tolerance.",
              },
              {
                icon: Code2,
                title: "Next.js 15 & React 19",
                desc: "Lightning fast App Router architecture with Tailwind CSS, Framer Motion, and React Query caching.",
              },
              {
                icon: Lock,
                title: "Enterprise Grade Security",
                desc: "JWT rotation, rate limiting with Redis, Google OAuth 2.0, and end-to-end data encryption.",
              },
            ].map((tech, i) => {
              const Icon = tech.icon;
              return (
                <div key={i} className="p-6 rounded-2xl bg-card border border-border">
                  <div className="p-2.5 rounded-xl bg-muted text-primary w-fit mb-3">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-bold text-foreground mb-1.5">{tech.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{tech.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Key Values */}
        <div className="p-8 sm:p-12 rounded-3xl bg-muted/30 border border-border">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">Our Core Principles</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-sm text-foreground mb-1">Zero Hallucination</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Answers are grounded in official gazettes, department portals, and verified regulatory guidelines.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto mb-3">
                <Users className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-sm text-foreground mb-1">Citizen First</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Designed to be intuitive for first-time applicants, elderly citizens, and rural communities across India.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center mx-auto mb-3">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-sm text-foreground mb-1">Privacy & Safety</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                We never store sensitive identity numbers (Aadhaar/PAN) or sell citizen data.
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center py-6">
          <Link
            href="/services"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all shadow-md"
          >
            Explore All Government Services <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
