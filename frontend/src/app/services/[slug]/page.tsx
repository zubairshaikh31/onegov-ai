"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Building2, CheckCircle, Clock, ExternalLink, FileText,
  HelpCircle, Info, Layers, Phone, Share2, Sparkles, Shield, Bookmark,
  AlertCircle, ChevronRight, CheckCircle2, Copy, Play
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import type { Service } from "@/types/government";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export default function ServiceDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<string>("overview");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["service", slug],
    queryFn: () => governmentApi.getServiceBySlug(slug),
  });

  const service = data?.data;

  const handleBookmark = async () => {
    if (!service) return;
    try {
      const res = await governmentApi.toggleBookmark("service", service.id);
      if (res.data?.bookmarked) {
        toast.success("Saved to bookmarks");
      } else {
        toast.info("Removed from bookmarks");
      }
    } catch {
      toast.error("Please log in to save bookmarks");
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

  if (isError || !service) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">🏛️</div>
          <h2 className="text-2xl font-bold text-foreground mb-2">Service Not Found</h2>
          <p className="text-muted-foreground text-sm mb-6">
            The requested government service may have been updated or moved.
          </p>
          <Link
            href="/services"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Directory
          </Link>
        </div>
      </div>
    );
  }

  const officialUrl = service.official_apply_link || service.official_url || "https://india.gov.in";

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header Bar */}
      <div className="border-b border-border bg-gradient-to-b from-muted/40 via-background to-background pt-24 pb-10 px-6">
        <div className="max-w-5xl mx-auto">
          <Link
            href="/services"
            className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground mb-6 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Services Directory
          </Link>

          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div>
              {/* Badges */}
              <div className="flex flex-wrap items-center gap-2 mb-3">
                {service.category && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                    <Building2 className="h-3.5 w-3.5" />
                    {service.category.name}
                  </span>
                )}
                {service.is_online && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-medium border border-emerald-500/20">
                    <CheckCircle2 className="h-3 w-3" />
                    100% Online
                  </span>
                )}
                {service.government_level && (
                  <span className="px-2.5 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                    {service.government_level} Government
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-4xl font-extrabold text-foreground tracking-tight mb-3">
                {service.name}
              </h1>

              {service.department && (
                <p className="text-muted-foreground text-sm flex items-center gap-2">
                  <span>Issued by:</span>
                  <span className="font-semibold text-foreground">{service.department.name}</span>
                  {service.ministry && <span>({service.ministry.name})</span>}
                </p>
              )}
            </div>

            {/* Top action buttons */}
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
                href={officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
              >
                Apply on Official Portal
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-card border border-border/80 shadow-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Processing Time</p>
              <p className="text-sm font-bold text-foreground">{service.processing_time || "10–15 Working Days"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Official Fee</p>
              <p className="text-sm font-bold text-foreground">{service.fee_description || "Standard Govt. Charge"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Application Mode</p>
              <p className="text-sm font-bold text-foreground">
                {service.is_online ? "Online Portal" : "In-Person / Office"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Helpline</p>
              <p className="text-sm font-bold text-foreground">{service.helpline_number || "1800-11-4000"}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content & Tabs */}
      <div className="max-w-5xl mx-auto px-6 mt-8">
        <div className="flex border-b border-border mb-8 overflow-x-auto no-scrollbar">
          {[
            { id: "overview", label: "Overview & Eligibility", icon: Info },
            { id: "documents", label: `Required Documents (${service.documents?.length || 0})`, icon: FileText },
            { id: "steps", label: `Application Steps (${service.application_steps?.length || 0})`, icon: Layers },
            { id: "faqs", label: `FAQs (${service.faqs?.length || 0})`, icon: HelpCircle },
            ...(service.videos && service.videos.length > 0 ? [{ id: "tutorials", label: `Video Tutorials (${service.videos.length})`, icon: Play }] : []),
          ].map((t) => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={cn(
                  "flex items-center gap-2 px-5 py-3 border-b-2 text-sm font-medium transition-colors whitespace-nowrap",
                  active
                    ? "border-primary text-primary font-bold"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Overview & Eligibility */}
        {activeTab === "overview" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            {/* Description */}
            <div className="p-6 rounded-2xl bg-card border border-border">
              <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
                <Info className="h-5 w-5 text-primary" />
                About This Service
              </h2>
              <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
                {service.description || service.short_description}
              </p>
            </div>

            {/* AI Assistant Callout */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-600/10 via-indigo-600/5 to-purple-600/10 border border-blue-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">
                  <Sparkles className="h-4 w-4" />
                  Intelligent Guidance
                </div>
                <h3 className="text-base font-bold text-foreground">Have questions about applying?</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Ask our AI Assistant for step-by-step troubleshooting, eligibility confirmation, or document advice.
                </p>
              </div>
              <Link
                href={`/ai-chat?topic=${encodeURIComponent(service.name)}`}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shrink-0"
              >
                <Sparkles className="h-4 w-4" />
                Ask about {service.name}
              </Link>
            </div>

            {/* Eligibility */}
            <div className="p-6 rounded-2xl bg-card border border-border">
              <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Eligibility Criteria
              </h2>
              <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
                {service.eligibility_description || "All eligible Indian citizens with valid proof of identity and residence."}
              </p>
            </div>

            {/* Benefits if present */}
            {service.benefits && (
              <div className="p-6 rounded-2xl bg-card border border-border">
                <h2 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-500" />
                  Key Benefits & Provisions
                </h2>
                <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">
                  {service.benefits}
                </p>
              </div>
            )}

            {/* Related Schemes & Services */}
            {service.related_schemes && service.related_schemes.length > 0 && (
              <div className="p-6 rounded-2xl bg-card border border-border">
                <h2 className="text-lg font-bold text-foreground mb-4">Related Welfare Schemes</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {service.related_schemes.map((sc) => (
                    <Link
                      key={sc.id}
                      href={`/schemes/${sc.slug}`}
                      className="p-4 rounded-xl bg-muted/40 hover:bg-muted border border-border transition-colors group flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">
                          {sc.name}
                        </p>
                        <p className="text-xs text-muted-foreground">{sc.target_beneficiary || "Welfare Scheme"}</p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Tab 2: Required Documents */}
        {activeTab === "documents" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {(!service.documents || service.documents.length === 0) ? (
              <div className="p-10 text-center bg-card border border-border rounded-2xl">
                <p className="text-sm text-muted-foreground">Standard KYC documents (Aadhaar, Address Proof, Photo) required.</p>
              </div>
            ) : (
              service.documents.map((doc, idx) => (
                <div key={doc.id || idx} className="p-5 rounded-2xl bg-card border border-border flex items-start gap-4">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary mt-0.5">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-bold text-foreground">{doc.name}</h3>
                      {doc.is_mandatory && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-destructive/10 text-destructive">
                          Mandatory
                        </span>
                      )}
                    </div>
                    {doc.description && <p className="text-xs text-muted-foreground mb-1">{doc.description}</p>}
                    {doc.notes && <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">Note: {doc.notes}</p>}
                  </div>
                </div>
              ))
            )}
          </motion.div>
        )}

        {/* Tab 3: Application Steps */}
        {activeTab === "steps" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {(!service.application_steps || service.application_steps.length === 0) ? (
              <div className="p-10 text-center bg-card border border-border rounded-2xl">
                <p className="text-sm text-muted-foreground">Apply online at the official government portal link above.</p>
              </div>
            ) : (
              service.application_steps.map((st, idx) => (
                <div key={idx} className="p-6 rounded-2xl bg-card border border-border flex items-start gap-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-xs shrink-0">
                    {st.step_number || idx + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-base font-bold text-foreground mb-1">{st.title}</h3>
                    <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                      {st.description}
                    </p>
                    {st.action_url && (
                      <a
                        href={st.action_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-primary mt-2 hover:underline"
                      >
                        Step Direct Link <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </motion.div>
        )}

        {/* Tab 4: FAQs */}
        {activeTab === "faqs" && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {(!service.faqs || service.faqs.length === 0) ? (
              <div className="p-10 text-center bg-card border border-border rounded-2xl">
                <p className="text-sm text-muted-foreground">No specific FAQs listed. You can ask our AI Assistant anytime.</p>
              </div>
            ) : (
              service.faqs.map((faq, idx) => (
                <details key={faq.id || idx} className="group p-5 rounded-2xl bg-card border border-border cursor-pointer">
                  <summary className="font-bold text-sm text-foreground list-none flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <HelpCircle className="h-4 w-4 text-primary" />
                      {faq.question}
                    </span>
                    <span className="transition-transform group-open:rotate-180 text-muted-foreground text-xs">▼</span>
                  </summary>
                  <p className="text-xs sm:text-sm text-muted-foreground mt-3 pl-6 leading-relaxed whitespace-pre-line">
                    {faq.answer}
                  </p>
                </details>
              ))
            )}
          </motion.div>
        )}

        {/* Tab 5: Video Tutorials */}
        {activeTab === "tutorials" && service.videos && service.videos.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {service.videos.map((vid: NonNullable<Service["videos"]>[number], idx: number) => (
              <div key={vid.id || idx} className="overflow-hidden rounded-2xl bg-card border border-border flex flex-col shadow-sm group">
                <div className="relative aspect-video bg-zinc-950 w-full overflow-hidden">
                  <iframe
                    className="w-full h-full border-0"
                    src={`https://www.youtube.com/embed/${vid.youtube_video_id}`}
                    title={vid.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-foreground mb-1 leading-snug group-hover:text-primary transition-colors">
                      {vid.title}
                    </h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Channel: <span className="font-semibold text-foreground/85">{vid.channel_name}</span>
                    </p>
                  </div>
                  <a
                    href={vid.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                  >
                    Watch on YouTube <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}
