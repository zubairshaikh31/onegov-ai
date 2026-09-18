"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bookmark, ArrowUpRight, Trash2, Building2, Gift, ChevronRight, ExternalLink
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { toast } from "sonner";

export default function BookmarksPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["user-bookmarks"],
    queryFn: () => governmentApi.getBookmarks(),
  });

  const removeMutation = useMutation({
    mutationFn: ({ type, id }: { type: "service" | "scheme"; id: string }) =>
      governmentApi.toggleBookmark(type, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-bookmarks"] });
      toast.success("Bookmark removed");
    },
  });

  const services = data?.data?.services || [];
  const schemes = data?.data?.schemes || [];
  const total = services.length + schemes.length;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Saved Bookmarks</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Quickly access your saved citizen services and welfare schemes ({total} saved).
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 rounded-2xl bg-muted/40 animate-pulse border border-border" />
          ))}
        </div>
      ) : total === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center rounded-3xl bg-card border border-border p-8">
          <Bookmark className="h-10 w-10 text-muted-foreground/40 mb-3" />
          <h2 className="text-base font-bold text-foreground mb-1">No bookmarks saved yet</h2>
          <p className="text-xs text-muted-foreground max-w-sm mb-6">
            Bookmark services and welfare schemes to track their application requirements and deadlines.
          </p>
          <div className="flex gap-3">
            <Link
              href="/services"
              className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors"
            >
              Browse Services
            </Link>
            <Link
              href="/schemes"
              className="px-4 py-2 rounded-xl bg-muted hover:bg-muted/80 text-foreground text-xs font-semibold transition-colors"
            >
              Browse Schemes
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Services Section */}
          {services.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-primary" />
                Bookmarked Services ({services.length})
              </h2>
              <div className="space-y-2">
                {services.map((svc) => (
                  <div
                    key={svc.id}
                    className="flex items-center justify-between p-4 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/services/${svc.slug}`}
                        className="font-bold text-sm text-foreground hover:text-primary transition-colors line-clamp-1"
                      >
                        {svc.name}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                        {svc.short_description || "Government Citizen Service"}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 pl-4">
                      <Link
                        href={`/services/${svc.slug}`}
                        className="p-2 rounded-xl text-muted-foreground hover:text-primary hover:bg-muted transition-colors"
                        title="View Service"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={() => removeMutation.mutate({ type: "service", id: svc.id })}
                        className="p-2 rounded-xl text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                        title="Remove bookmark"
                        aria-label="Remove bookmark"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Schemes Section */}
          {schemes.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Gift className="h-3.5 w-3.5 text-primary" />
                Bookmarked Schemes ({schemes.length})
              </h2>
              <div className="space-y-2">
                {schemes.map((sc) => (
                  <div
                    key={sc.id}
                    className="flex items-center justify-between p-4 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/schemes/${sc.slug}`}
                        className="font-bold text-sm text-foreground hover:text-primary transition-colors line-clamp-1"
                      >
                        {sc.name}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                        {sc.benefit_amount ? `Benefit: ${sc.benefit_amount}` : sc.target_beneficiary || "Welfare Scheme"}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 pl-4">
                      <Link
                        href={`/schemes/${sc.slug}`}
                        className="p-2 rounded-xl text-muted-foreground hover:text-primary hover:bg-muted transition-colors"
                        title="View Scheme"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={() => removeMutation.mutate({ type: "scheme", id: sc.id })}
                        className="p-2 rounded-xl text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                        title="Remove bookmark"
                        aria-label="Remove bookmark"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
