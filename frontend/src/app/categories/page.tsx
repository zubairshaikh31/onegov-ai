"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Folder, Shield, HeartPulse, Tractor, Car, Briefcase, GraduationCap,
  Building, Home, Scale, Landmark, Sparkles, ChevronRight, ArrowRight
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import type { Category } from "@/types/government";

const CATEGORY_ICONS: Record<string, any> = {
  identity: Shield,
  agriculture: Tractor,
  healthcare: HeartPulse,
  transport: Car,
  business: Briefcase,
  education: GraduationCap,
  housing: Home,
  legal: Scale,
  finance: Landmark,
  municipal: Building,
};

export default function CategoriesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: () => governmentApi.getCategories(),
  });

  const categories = data?.data || [];

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header */}
      <div className="border-b border-border bg-gradient-to-b from-muted/50 to-background pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary mb-3">
            <Folder className="h-3.5 w-3.5" />
            Service Taxonomy
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Browse by Category
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
            Explore government services and welfare schemes organized across primary civic and administrative categories.
          </p>
        </div>
      </div>

      {/* Grid */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-44 rounded-2xl bg-muted/40 border border-border animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {categories.map((cat) => {
              const Icon = CATEGORY_ICONS[cat.slug] || Folder;
              return (
                <Link
                  key={cat.id}
                  href={`/services?category=${cat.slug}`}
                  className="group p-6 rounded-2xl bg-card hover:bg-muted/40 border border-border hover:border-primary/40 transition-all duration-300 shadow-sm hover:shadow-md flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-3 rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        <Icon className="h-6 w-6" />
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-muted text-muted-foreground">
                        {cat.services_count || 0} services
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-foreground mb-1 group-hover:text-primary transition-colors">
                      {cat.name}
                    </h3>
                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                      {cat.description || "Official citizen services, permits, registrations, and schemes."}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs font-semibold text-primary">
                    <span>Explore services</span>
                    <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
