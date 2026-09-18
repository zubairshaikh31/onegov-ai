"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search, Shield, Users, Gift, CheckCircle2, ChevronRight, Bookmark,
  Sparkles, ExternalLink, Filter, Building2, ArrowRight
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import type { Scheme } from "@/types/government";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function SchemesContent() {
  const searchParams = useSearchParams();
  const initialType = searchParams.get("type") || "";
  const initialQuery = searchParams.get("q") || "";

  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [schemeType, setSchemeType] = useState(initialType);
  const [beneficiary, setBeneficiary] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["schemes", searchQuery, schemeType, beneficiary, page],
    queryFn: () =>
      governmentApi.getSchemes({
        q: searchQuery || undefined,
        scheme_type: schemeType || undefined,
        beneficiary: beneficiary || undefined,
        page,
        page_size: 15,
      }),
  });

  const schemes = data?.data?.items || [];
  const total = data?.data?.total || 0;
  const totalPages = data?.data?.total_pages || 1;

  const handleBookmark = async (e: React.MouseEvent, sc: Scheme) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const res = await governmentApi.toggleBookmark("scheme", sc.id);
      if (res.data?.bookmarked) {
        toast.success(`Saved "${sc.name}" to bookmarks`);
      } else {
        toast.info(`Removed "${sc.name}" from bookmarks`);
      }
    } catch {
      toast.error("Please login to save bookmarks");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary mb-3">
                <Gift className="h-3.5 w-3.5" />
                Citizen Welfare & Subsidies
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-3">
                Government Schemes
              </h1>
              <p className="text-muted-foreground text-sm sm:text-base max-w-2xl leading-relaxed">
                Find Central and State Government welfare schemes, financial aid, agricultural subsidies, healthcare insurance, and educational scholarships.
              </p>
            </div>
            <Link
              href="/ai-chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm self-start md:self-auto"
            >
              <Sparkles className="h-4 w-4" />
              Check My Eligibility
            </Link>
          </div>

          {/* Search and Filters */}
          <div className="mt-8 flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search schemes (e.g. PM Kisan, Ayushman Bharat, Awas, Ladki Bahin, Scholarship)..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-card border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-sm"
              />
            </div>

            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <select
                value={schemeType}
                onChange={(e) => {
                  setSchemeType(e.target.value);
                  setPage(1);
                }}
                aria-label="Filter by scheme jurisdiction"
                className="px-3.5 py-3 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="">All Jurisdictions</option>
                <option value="central">Central Schemes</option>
                <option value="state">State Schemes</option>
              </select>

              <select
                value={beneficiary}
                onChange={(e) => {
                  setBeneficiary(e.target.value);
                  setPage(1);
                }}
                aria-label="Filter by target beneficiary"
                className="px-3.5 py-3 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="">All Beneficiaries</option>
                <option value="farmers">Farmers</option>
                <option value="women">Women</option>
                <option value="senior">Senior Citizens</option>
                <option value="students">Students / Youth</option>
                <option value="bpl">Low Income / BPL</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-64 rounded-2xl bg-muted/40 border border-border animate-pulse" />
            ))}
          </div>
        ) : schemes.length === 0 ? (
          <div className="text-center py-20 bg-muted/20 border border-border rounded-3xl p-8">
            <div className="text-4xl mb-3">🏛️</div>
            <h3 className="text-lg font-bold text-foreground mb-1">No schemes found</h3>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto mb-6">
              Try modifying your search or clearing the beneficiary filter.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSchemeType("");
                setBeneficiary("");
              }}
              className="px-4 py-2 rounded-xl bg-muted hover:bg-muted/80 text-xs font-semibold"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {schemes.map((sc) => (
                <Link
                  key={sc.id}
                  href={`/schemes/${sc.slug}`}
                  className="group relative flex flex-col justify-between p-6 rounded-2xl bg-card hover:bg-muted/30 border border-border/80 hover:border-primary/40 transition-all duration-300 shadow-sm hover:shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 text-[11px] font-semibold text-primary">
                        <Users className="h-3 w-3" />
                        {sc.target_beneficiary || "Citizens"}
                      </span>

                      <button
                        onClick={(e) => handleBookmark(e, sc)}
                        className="p-1.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                        title="Bookmark scheme"
                        aria-label="Bookmark scheme"
                      >
                        <Bookmark className="h-4 w-4" />
                      </button>
                    </div>

                    <h3 className="text-lg font-bold text-foreground mb-2 group-hover:text-primary transition-colors line-clamp-1">
                      {sc.name}
                    </h3>

                    <p className="text-muted-foreground text-xs leading-relaxed line-clamp-3 mb-4">
                      {sc.short_description || sc.description || "Government welfare assistance scheme."}
                    </p>

                    {sc.benefit_amount && (
                      <div className="mb-4 inline-block px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                        Benefit: {sc.benefit_amount}
                      </div>
                    )}
                  </div>

                  <div className="pt-4 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                    <span className="capitalize">{sc.scheme_type || "Central"} Scheme</span>
                    <span className="flex items-center gap-1 font-semibold text-primary group-hover:translate-x-1 transition-transform">
                      Check eligibility
                      <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-12 flex items-center justify-center gap-2">
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
          </>
        )}
      </div>
    </div>
  );
}

export default function SchemesPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
      <SchemesContent />
    </Suspense>
  );
}
