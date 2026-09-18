"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search, Filter, Globe, Building2, CheckCircle2, ChevronRight, Bookmark,
  Share2, ArrowUpRight, Sparkles, SlidersHorizontal, ArrowLeft,
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import type { Service, Category } from "@/types/government";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function ServicesContent() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get("category") || "";
  const initialQuery = searchParams.get("q") || "";

  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [onlineOnly, setOnlineOnly] = useState(false);
  const [sortBy, setSortBy] = useState("featured");
  const [page, setPage] = useState(1);

  // Fetch categories for filtering
  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => governmentApi.getCategories(),
  });

  // Fetch services
  const { data: servicesData, isLoading } = useQuery({
    queryKey: ["services", searchQuery, selectedCategory, onlineOnly, sortBy, page],
    queryFn: () =>
      governmentApi.getServices({
        q: searchQuery || undefined,
        category_slug: selectedCategory || undefined,
        is_online: onlineOnly ? true : undefined,
        sort_by: sortBy,
        page,
        page_size: 15,
      }),
  });

  const categories = categoriesData?.data || [];
  const services = servicesData?.data?.items || [];
  const total = servicesData?.data?.total || 0;
  const totalPages = servicesData?.data?.total_pages || 1;

  const handleBookmarkToggle = async (e: React.MouseEvent, svc: Service) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const res = await governmentApi.toggleBookmark("service", svc.id);
      if (res.data?.bookmarked) {
        toast.success(`Saved "${svc.name}" to bookmarks`);
      } else {
        toast.info(`Removed "${svc.name}" from bookmarks`);
      }
    } catch {
      toast.error("Please login to save bookmarks");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header Banner */}
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary mb-3">
                <Sparkles className="h-3.5 w-3.5" />
                Verified Digital Directory
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-3">
                Government Services
              </h1>
              <p className="text-muted-foreground text-sm sm:text-base max-w-2xl leading-relaxed">
                Discover, apply, and track all Central & State government citizen services with step-by-step guidance and document checklists.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/ai-chat"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
              >
                <Sparkles className="h-4 w-4" />
                Ask AI Assistant
              </Link>
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="mt-8 flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search services by name, keyword, department (e.g. Passport, Aadhaar, Licence)..."
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
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                aria-label="Sort services by"
                className="px-3.5 py-3 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="featured">Featured First</option>
                <option value="popular">Most Popular</option>
                <option value="name">Alphabetical (A-Z)</option>
                <option value="newest">Recently Added</option>
              </select>

              <button
                onClick={() => setOnlineOnly(!onlineOnly)}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-colors whitespace-nowrap",
                  onlineOnly
                    ? "bg-primary/10 border-primary text-primary"
                    : "bg-card border-border text-muted-foreground hover:text-foreground"
                )}
              >
                <Globe className="h-4 w-4" />
                Online Only
              </button>
            </div>
          </div>

          {/* Category Pills */}
          <div className="mt-4 flex items-center gap-2 overflow-x-auto no-scrollbar pb-2">
            <button
              onClick={() => {
                setSelectedCategory("");
                setPage(1);
              }}
              className={cn(
                "px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap",
                selectedCategory === ""
                  ? "bg-foreground text-background"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              All Categories ({total})
            </button>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => {
                  setSelectedCategory(cat.slug);
                  setPage(1);
                }}
                className={cn(
                  "px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap",
                  selectedCategory === cat.slug
                    ? "bg-foreground text-background"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                )}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-64 rounded-2xl bg-muted/40 border border-border animate-pulse"
              />
            ))}
          </div>
        ) : services.length === 0 ? (
          <div className="text-center py-20 bg-muted/20 border border-border rounded-3xl p-8">
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="text-lg font-bold text-foreground mb-1">No services found</h3>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto mb-6">
              Try adjusting your search keywords or resetting category filters.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("");
                setOnlineOnly(false);
              }}
              className="px-4 py-2 rounded-xl bg-muted hover:bg-muted/80 text-xs font-semibold"
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((svc) => (
                <Link
                  key={svc.id}
                  href={`/services/${svc.slug}`}
                  className="group relative flex flex-col justify-between p-6 rounded-2xl bg-card hover:bg-muted/30 border border-border/80 hover:border-primary/40 transition-all duration-300 shadow-sm hover:shadow-md"
                >
                  <div>
                    {/* Top Row: Category badge & Bookmark */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted text-[11px] font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                        <Building2 className="h-3 w-3" />
                        {svc.category?.name || "General Service"}
                      </span>

                      <button
                        onClick={(e) => handleBookmarkToggle(e, svc)}
                        className="p-1.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                        title="Save to bookmarks"
                        aria-label="Bookmark service"
                      >
                        <Bookmark className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Name */}
                    <h3 className="text-lg font-bold text-foreground mb-2 group-hover:text-primary transition-colors line-clamp-1">
                      {svc.name}
                    </h3>

                    {/* Description */}
                    <p className="text-muted-foreground text-xs leading-relaxed line-clamp-3 mb-4">
                      {svc.short_description || svc.description || "Official government portal application and citizen service."}
                    </p>
                  </div>

                  {/* Bottom Meta */}
                  <div className="pt-4 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      {svc.is_online && (
                        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Online Portal
                        </span>
                      )}
                      {svc.processing_time && (
                        <span className="text-muted-foreground">• {svc.processing_time}</span>
                      )}
                    </div>

                    <span className="flex items-center gap-1 font-semibold text-primary group-hover:translate-x-1 transition-transform">
                      View details
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

export default function ServicesPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
      <ServicesContent />
    </Suspense>
  );
}
