"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Sparkles, Building2, Shield, Gift, HelpCircle, ArrowRight,
  ExternalLink, ChevronRight, Filter, Globe, RotateCcw
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import type { SearchResult } from "@/types/government";
import { cn } from "@/lib/utils";

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryParam = searchParams.get("q") || "";

  const [query, setQuery] = useState(queryParam);
  const [debouncedQuery, setDebouncedQuery] = useState(queryParam);
  const [activeType, setActiveType] = useState<string>("all");
  const [page, setPage] = useState(1);

  // Debounce input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
      if (query.trim()) {
        router.replace(`/search?q=${encodeURIComponent(query.trim())}`, { scroll: false });
      }
    }, 250);
    return () => clearTimeout(handler);
  }, [query, router]);

  // Fetch search suggestions
  const { data: suggestionsData } = useQuery({
    queryKey: ["search-suggestions", query],
    queryFn: () => governmentApi.getSearchSuggestions(query),
    enabled: query.trim().length >= 2,
  });

  // Fetch popular searches
  const { data: popularData } = useQuery({
    queryKey: ["popular-searches"],
    queryFn: () => governmentApi.getPopularSearches(),
  });

  // Main search query
  const { data: searchData, isLoading } = useQuery({
    queryKey: ["global-search", debouncedQuery, activeType, page],
    queryFn: () =>
      governmentApi.search({
        q: debouncedQuery,
        type: activeType,
        page,
        page_size: 20,
      }),
    enabled: debouncedQuery.trim().length > 0,
  });

  const results = searchData?.data?.results || [];
  const total = searchData?.data?.total || 0;
  const totalPages = searchData?.data?.total_pages || 1;
  const suggestions = suggestionsData?.data;
  const trending = popularData?.data?.trending || [];

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Search Header */}
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-8 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-6">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
              Global Intelligent Search
            </h1>
            <p className="text-muted-foreground text-sm max-w-md mx-auto">
              Instant semantic & keyword discovery across 1,000+ government services, welfare schemes, and official FAQs.
            </p>
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              autoFocus
              placeholder="Search by name, eligibility, documents, or question (e.g. Passport renewal, PM Kisan, Ladki Bahin)..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              className="w-full pl-12 pr-10 py-4 rounded-2xl bg-card border border-border text-base placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary shadow-lg transition-all"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted"
                aria-label="Clear search query"
              >
                ✕
              </button>
            )}
          </div>

          {/* Type Filter Pills */}
          <div className="mt-4 flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
            {[
              { id: "all", label: "All Results" },
              { id: "service", label: "Services" },
              { id: "scheme", label: "Welfare Schemes" },
              { id: "faq", label: "FAQs" },
              { id: "ministry", label: "Ministries" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  setActiveType(t.id);
                  setPage(1);
                }}
                className={cn(
                  "px-4 py-2 rounded-xl text-xs font-semibold transition-colors whitespace-nowrap",
                  activeType === t.id
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "bg-card hover:bg-muted text-muted-foreground hover:text-foreground border border-border"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {!debouncedQuery.trim() ? (
          /* Empty / Initial State with Trending searches */
          <div className="py-8 space-y-8">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                Popular Searches
              </h2>
              <div className="flex flex-wrap gap-2">
                {trending.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => setQuery(item)}
                    className="px-3.5 py-2 rounded-xl bg-card hover:bg-muted border border-border text-xs font-medium text-foreground transition-colors"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            {/* AI Assistant Promo Card */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-600/10 via-indigo-600/5 to-purple-600/10 border border-blue-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-foreground mb-1">Looking for personalized guidance?</h3>
                <p className="text-xs text-muted-foreground">
                  Our RAG AI Chatbot can analyze your exact situation and guide you to the right government schemes.
                </p>
              </div>
              <Link
                href="/ai-chat"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold whitespace-nowrap hover:bg-primary/90 transition-colors"
              >
                <Sparkles className="h-4 w-4" />
                Start AI Consultation
              </Link>
            </div>
          </div>
        ) : isLoading ? (
          <div className="space-y-4 py-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-28 rounded-2xl bg-muted/40 border border-border animate-pulse" />
            ))}
          </div>
        ) : results.length === 0 ? (
          <div className="text-center py-16 bg-muted/20 border border-border rounded-3xl p-8">
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="text-lg font-bold text-foreground mb-1">No exact matches found</h3>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto mb-6">
              We couldn&apos;t find results for &quot;{debouncedQuery}&quot;. Try checking for spelling or asking our AI Assistant.
            </p>
            <Link
              href={`/ai-chat?topic=${encodeURIComponent(debouncedQuery)}`}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold"
            >
              <Sparkles className="h-4 w-4" />
              Ask AI Assistant about &quot;{debouncedQuery}&quot;
            </Link>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
              <span>Found {total} results for &quot;{debouncedQuery}&quot;</span>
              <span>Page {page} of {totalPages}</span>
            </div>

            <div className="space-y-3">
              {results.map((res, i) => {
                const isService = res.type === "service";
                const isScheme = res.type === "scheme";
                const isFaq = res.type === "faq";
                const isMinistry = res.type === "ministry";

                return (
                  <Link
                    key={`${res.type}-${res.id}-${i}`}
                    href={res.url}
                    className="group block p-5 rounded-2xl bg-card hover:bg-muted/40 border border-border hover:border-primary/40 transition-all duration-200 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider",
                            isService && "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20",
                            isScheme && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20",
                            isFaq && "bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20",
                            isMinistry && "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                          )}
                        >
                          {res.type}
                        </span>
                        {res.category && (
                          <span className="text-xs text-muted-foreground">{res.category}</span>
                        )}
                        {res.target_beneficiary && (
                          <span className="text-xs text-muted-foreground">For: {res.target_beneficiary}</span>
                        )}
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                    </div>

                    <h3 className="text-base font-bold text-foreground mb-1 group-hover:text-primary transition-colors">
                      {res.name || res.question}
                    </h3>

                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                      {res.description || res.answer}
                    </p>

                    {res.fee_description && (
                      <div className="mt-2 text-[11px] font-medium text-foreground/80">
                        Fee: {res.fee_description}
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-4 py-2 rounded-xl border border-border text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-muted"
                >
                  Previous
                </button>
                <span className="text-xs text-muted-foreground px-3">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-4 py-2 rounded-xl border border-border text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-muted"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
      <SearchContent />
    </Suspense>
  );
}
