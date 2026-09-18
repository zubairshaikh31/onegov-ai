"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Building2, CheckCircle2, ExternalLink, FileText, Gift,
  HelpCircle, Info, Shield, Sparkles, Users, Bookmark, Share2, ChevronRight
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export default function SchemeDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["scheme", slug],
    queryFn: () => governmentApi.getSchemeBySlug(slug),
  });

  const scheme = data?.data;

  const handleBookmark = async () => {
    if (!scheme) return;
    try {
      const res = await governmentApi.toggleBookmark("scheme", scheme.id);
      if (res.data?.bookmarked) {
        toast.success("Saved scheme to bookmarks");
      } else {
        toast.info("Removed scheme from bookmarks");
      }
    } catch {
      toast.error("Please log in to bookmark");
    }
  };

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard!");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background pt-28 px-6">
        <div className="max-w-5xl mx-auto space-y-6 animate-pulse">
          <div className="h-6 w-32 bg-muted rounded-lg" />
          <div className="h-12 w-3/4 bg-muted rounded-xl" />
          <div className="h-48 bg-muted rounded-2xl" />
        </div>
      </div>
    );
  }

  if (isError || !scheme) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">🏛️</div>
          <h2 className="text-2xl font-bold text-foreground mb-2">Scheme Not Found</h2>
          <p className="text-muted-foreground text-sm mb-6">
            The requested welfare scheme may have been concluded or reorganized.
          </p>
          <Link
            href="/schemes"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Schemes
          </Link>
        </div>
      </div>
    );
  }

  const portalUrl = scheme.official_portal || scheme.official_url || "https://india.gov.in";

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header */}
      <div className="border-b border-border bg-gradient-to-b from-muted/40 via-background to-background pt-24 pb-10 px-6">
        <div className="max-w-5xl mx-auto">
          <Link
            href="/schemes"
            className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground mb-6 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Schemes Directory
          </Link>

          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                  <Users className="h-3.5 w-3.5" />
                  {scheme.target_beneficiary || "Citizens"}
                </span>
                <span className="px-2.5 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium uppercase">
                  {scheme.scheme_type || "Central"} Scheme
                </span>
              </div>

              <h1 className="text-2xl sm:text-4xl font-extrabold text-foreground tracking-tight mb-3">
                {scheme.name}
              </h1>

              {scheme.ministry && (
                <p className="text-muted-foreground text-sm flex items-center gap-2">
                  <span>Administered by:</span>
                  <span className="font-semibold text-foreground">{scheme.ministry.name}</span>
                </p>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleBookmark}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border border-border text-sm font-medium hover:bg-muted text-foreground transition-colors shadow-sm"
              >
                <Bookmark className="h-4 w-4" />
                Bookmark
              </button>

              <button
                onClick={handleShare}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border border-border text-sm font-medium hover:bg-muted text-foreground transition-colors shadow-sm"
              >
                <Share2 className="h-4 w-4" />
                Share
              </button>

              <a
                href={portalUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
              >
                Official Portal
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Benefit Badge */}
          {scheme.benefit_amount && (
            <div className="mt-6 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-emerald-800 dark:text-emerald-300">Financial Aid / Benefit</p>
                <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{scheme.benefit_amount}</p>
              </div>
              <div className="text-2xl">💰</div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 mt-8 space-y-8">
        {/* Description */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
            <Info className="h-5 w-5 text-primary" />
            Scheme Details & Objectives
          </h2>
          <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
            {scheme.description || scheme.short_description}
          </p>
        </div>

        {/* AI Eligibility Checker Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-600/10 via-blue-600/5 to-indigo-600/10 border border-purple-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-purple-600 dark:text-purple-400 mb-1">
              <Sparkles className="h-4 w-4" />
              Instant Eligibility Check
            </div>
            <h3 className="text-base font-bold text-foreground">Want to know if you qualify?</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Our AI verifies your family income, occupation, and state rules to give you a definitive answer.
            </p>
          </div>
          <Link
            href={`/ai-chat?topic=${encodeURIComponent(`Check my eligibility for ${scheme.name}`)}`}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold transition-colors shrink-0"
          >
            <Sparkles className="h-4 w-4" />
            Verify My Eligibility
          </Link>
        </div>

        {/* Eligibility Criteria */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Eligibility Criteria
          </h2>
          <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
            {scheme.eligibility_description || "Targeted to Indian citizens meeting beneficiary parameters."}
          </p>
        </div>

        {/* Benefits Description */}
        {scheme.benefits_description && (
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
              <Gift className="h-5 w-5 text-emerald-500" />
              Detailed Benefits
            </h2>
            <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
              {scheme.benefits_description}
            </p>
          </div>
        )}

        {/* Linked Service */}
        {scheme.service && (
          <div className="p-6 rounded-2xl bg-card border border-border flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Associated Application Portal</p>
              <h3 className="text-base font-bold text-foreground">{scheme.service.name}</h3>
            </div>
            <Link
              href={`/services/${scheme.service.slug}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold"
            >
              Go to Service <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
