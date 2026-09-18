"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Gift, Plus, Search, Trash2, ExternalLink, Users, Sparkles
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { toast } from "sonner";

export default function AdminSchemesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    short_description: "",
    description: "",
    target_beneficiary: "",
    benefit_amount: "",
    scheme_type: "central",
    official_url: "",
    is_featured: false,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["admin-schemes-list", search, page],
    queryFn: () => governmentApi.getSchemes({ q: search || undefined, page, page_size: 15 }),
  });

  const createMutation = useMutation({
    mutationFn: (body: any) => governmentApi.createScheme(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-schemes-list"] });
      toast.success("Scheme created successfully!");
      setIsModalOpen(false);
      setForm({
        name: "",
        slug: "",
        short_description: "",
        description: "",
        target_beneficiary: "",
        benefit_amount: "",
        scheme_type: "central",
        official_url: "",
        is_featured: false,
      });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || "Failed to create scheme");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => governmentApi.deleteScheme(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-schemes-list"] });
      toast.success("Scheme deleted.");
    },
    onError: () => toast.error("Failed to delete scheme"),
  });

  const schemes = data?.data?.items || [];
  const total = data?.data?.total || 0;
  const totalPages = data?.data?.total_pages || 1;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.slug) {
      toast.error("Name and Slug are required.");
      return;
    }
    createMutation.mutate(form);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Welfare Schemes Management</h1>
          <p className="text-sm text-muted-foreground">Manage welfare subsidies, pensions, and financial aid schemes ({total} total)</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          Add Scheme
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Filter schemes by name..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/50 border-b border-border text-muted-foreground font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-4">Scheme Name</th>
                <th className="p-4">Beneficiary</th>
                <th className="p-4">Benefit</th>
                <th className="p-4">Type</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    Loading schemes...
                  </td>
                </tr>
              ) : schemes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    No schemes found.
                  </td>
                </tr>
              ) : (
                schemes.map((sc) => (
                  <tr key={sc.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-4 font-semibold text-foreground">
                      <div>{sc.name}</div>
                      <div className="text-[11px] text-muted-foreground font-mono font-normal">{sc.slug}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{sc.target_beneficiary || "Citizens"}</td>
                    <td className="p-4 font-semibold text-emerald-600 dark:text-emerald-400">
                      {sc.benefit_amount || "Financial Aid"}
                    </td>
                    <td className="p-4 capitalize text-muted-foreground">{sc.scheme_type || "Central"}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/schemes/${sc.slug}`}
                          target="_blank"
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
                          title="View scheme"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => {
                            if (confirm(`Delete scheme "${sc.name}"?`)) {
                              deleteMutation.mutate(sc.id);
                            }
                          }}
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Scheme Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-3xl bg-card border border-border p-6 shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-foreground">Add New Welfare Scheme</h2>
            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">Scheme Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. PM Surya Ghar Muft Bijli Yojana"
                  value={form.name}
                  onChange={(e) => {
                    const name = e.target.value;
                    const slug = name.toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
                    setForm({ ...form, name, slug });
                  }}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Slug *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. pm-surya-ghar"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Target Beneficiary</label>
                <input
                  type="text"
                  placeholder="e.g. Residential households, Farmers"
                  value={form.target_beneficiary}
                  onChange={(e) => setForm({ ...form, target_beneficiary: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Benefit Amount / Subsidy</label>
                <input
                  type="text"
                  placeholder="e.g. Up to ₹78,000 subsidy"
                  value={form.benefit_amount}
                  onChange={(e) => setForm({ ...form, benefit_amount: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Official Portal URL</label>
                <input
                  type="url"
                  placeholder="https://pmsuryaghar.gov.in"
                  value={form.official_url}
                  onChange={(e) => setForm({ ...form, official_url: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-border hover:bg-muted text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 disabled:opacity-50"
                >
                  {createMutation.isPending ? "Saving..." : "Save Scheme"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
