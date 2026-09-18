"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search, HelpCircle, Sparkles, ChevronDown, ChevronRight, ArrowRight } from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { cn } from "@/lib/utils";

const GENERAL_FAQS = [
  {
    question: "What is OneGov AI and how does it help citizens?",
    answer: "OneGov AI is an intelligent civic assistance platform that indexes Central and State government services, welfare schemes, and application guidelines. It helps you check eligibility, prepare required document checklists, and navigate official government portals without confusion.",
  },
  {
    question: "Does OneGov AI charge any fee for application guidance?",
    answer: "No. OneGov AI is completely free for citizens. You only pay official government statutory fees directly on the verified government portal (e.g. Passport Seva, Parivahan, UIDAI) when submitting your application.",
  },
  {
    question: "How does the AI Assistant verify eligibility for welfare schemes?",
    answer: "Our AI Assistant references the latest official Government of India gazettes, scheme guidelines (like PM Kisan, Ayushman Bharat, PM Awas), income thresholds, and age criteria to evaluate if you or your family qualify.",
  },
  {
    question: "Is my personal data safe on OneGov AI?",
    answer: "Yes. We operate on a zero-retention policy for sensitive citizen identifiers. We never ask for, require, or store full Aadhaar numbers, biometric data, or banking passwords.",
  },
  {
    question: "Can I apply for services directly through this website?",
    answer: "OneGov AI guides you through preparation and directs you directly to the official ministry/department portal (e.g. passportindia.gov.in, uidai.gov.in) to submit and pay officially.",
  },
  {
    question: "What should I do if a government office rejects my document?",
    answer: "Check our Service Details page for the exact list of acceptable alternative proofs (e.g. Voter ID, Bank Passbook with photograph, Electricity Bill) or ask our AI Assistant for state-specific gazetted alternatives.",
  },
];

export default function FAQPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const { data: serverFaqs } = useQuery({
    queryKey: ["faqs", searchQuery],
    queryFn: () => governmentApi.getFaqs({ q: searchQuery || undefined, page_size: 20 }),
  });

  const liveFaqs = serverFaqs?.data?.items || [];
  const displayFaqs = searchQuery.trim() ? liveFaqs : (liveFaqs.length > 0 ? liveFaqs.slice(0, 15) : GENERAL_FAQS);

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header */}
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-12 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary mb-3">
            <HelpCircle className="h-3.5 w-3.5" />
            Frequently Asked Questions
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-4">
            How can we help you?
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mb-8">
            Find immediate answers about government application procedures, eligibility, required documents, and portals.
          </p>

          {/* Search Bar */}
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search questions (e.g. Passport tatkaal, Aadhaar mobile update, PM Kisan)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-card border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary shadow-sm"
            />
          </div>
        </div>
      </div>

      {/* FAQs Accordion */}
      <div className="max-w-4xl mx-auto px-6 py-12 space-y-4">
        {displayFaqs.length === 0 ? (
          <div className="text-center py-16 bg-muted/20 border border-border rounded-3xl p-8">
            <h3 className="text-base font-bold text-foreground mb-2">No matching questions found</h3>
            <p className="text-xs text-muted-foreground mb-4">
              Have a specific question? Ask our AI Assistant for an instant, customized answer.
            </p>
            <Link
              href={`/ai-chat?topic=${encodeURIComponent(searchQuery)}`}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold"
            >
              <Sparkles className="h-4 w-4" />
              Ask AI Assistant
            </Link>
          </div>
        ) : (
          displayFaqs.map((faq, i) => {
            const isOpen = openIndex === i;
            return (
              <div
                key={i}
                className="rounded-2xl bg-card border border-border overflow-hidden transition-colors"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  className="w-full p-5 text-left flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-foreground hover:text-primary transition-colors"
                >
                  <span className="flex items-center gap-3">
                    <span className="text-primary font-mono text-xs">Q{i + 1}.</span>
                    {faq.question}
                  </span>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 text-muted-foreground transition-transform shrink-0",
                      isOpen && "rotate-180 text-primary"
                    )}
                  />
                </button>
                {isOpen && (
                  <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/40 whitespace-pre-line">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* AI Banner */}
        <div className="mt-12 p-8 rounded-3xl bg-gradient-to-r from-blue-600/10 via-indigo-600/5 to-purple-600/10 border border-blue-500/20 text-center">
          <Sparkles className="h-8 w-8 text-primary mx-auto mb-3" />
          <h3 className="text-lg font-bold text-foreground mb-1">Didn&apos;t find what you were looking for?</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto mb-6">
            Our AI Assistant is available 24/7 to answer complex citizen questions across 1,000+ government services.
          </p>
          <Link
            href="/ai-chat"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm"
          >
            Start Free AI Consultation <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
