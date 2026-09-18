"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2, Plus, Search, Trash2, Edit3, ExternalLink, Globe, CheckCircle2
} from "lucide-react";
import { governmentApi } from "@/lib/api/government";
import { toast } from "sonner";

export default function AdminServicesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    short_description: "",
    description: "",
    official_url: "",
    fee_description: "",
    processing_time: "",
    is_online: true,
    is_featured: false,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["admin-services-list", search, page],
    queryFn: () => governmentApi.getServices({ q: search || undefined, page, page_size: 15 }),
  });

  const createMutation = useMutation({
    mutationFn: (body: any) => governmentApi.createService(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-services-list"] });
      toast.success("Service created successfully!");
      setIsModalOpen(false);
      setForm({
        name: "",
        slug: "",
        short_description: "",
        description: "",
        official_url: "",
        fee_description: "",
        processing_time: "",
        is_online: true,
        is_featured: false,
      });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || "Failed to create service");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => governmentApi.deleteService(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-services-list"] });
      toast.success("Service deleted.");
    },
    onError: () => toast.error("Failed to delete service"),
  });

  const services = data?.data?.items || [];
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
          <h1 className="text-2xl font-bold text-foreground">Services Management</h1>
          <p className="text-sm text-muted-foreground">Manage and publish government citizen services ({total} total)</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          Add Service
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Filter services by name..."
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
                <th className="p-4">Service Name</th>
                <th className="p-4">Category</th>
                <th className="p-4">Mode</th>
                <th className="p-4">Views</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    Loading services catalog...
                  </td>
                </tr>
              ) : services.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    No services found.
                  </td>
                </tr>
              ) : (
                services.map((svc) => (
                  <tr key={svc.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-4 font-semibold text-foreground">
                      <div>{svc.name}</div>
                      <div className="text-[11px] text-muted-foreground font-mono font-normal">{svc.slug}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{svc.category?.name || "General"}</td>
                    <td className="p-4">
                      {svc.is_online ? (
                        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="h-3 w-3" /> Online
                        </span>
                      ) : (
                        <span className="text-muted-foreground">Offline</span>
                      )}
                    </td>
                    <td className="p-4 text-muted-foreground font-mono">{svc.view_count || 0}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/services/${svc.slug}`}
                          target="_blank"
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
                          title="View on site"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => {
                            if (confirm(`Delete "${svc.name}"?`)) {
                              deleteMutation.mutate(svc.id);
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
            <span>Showing page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40"
              >
                Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Service Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-3xl bg-card border border-border p-6 shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-foreground">Add New Government Service</h2>
            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">Service Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Voter ID Online Application"
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
                  placeholder="e.g. voter-id-apply"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Short Description</label>
                <input
                  type="text"
                  placeholder="Brief summary for listings..."
                  value={form.short_description}
                  onChange={(e) => setForm({ ...form, short_description: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div>
                <label className="block font-semibold mb-1">Official Portal URL</label>
                <input
                  type="url"
                  placeholder="https://..."
                  value={form.official_url}
                  onChange={(e) => setForm({ ...form, official_url: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-background border border-border"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Fee Description</label>
                  <input
                    type="text"
                    placeholder="Free / ₹50"
                    value={form.fee_description}
                    onChange={(e) => setForm({ ...form, fee_description: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-background border border-border"
                  />
                </div>
                <div>
                  <label className="block font-semibold mb-1">Processing Time</label>
                  <input
                    type="text"
                    placeholder="15 working days"
                    value={form.processing_time}
                    onChange={(e) => setForm({ ...form, processing_time: e.target.value })}
                    className="w-full p-2.5 rounded-xl bg-background border border-border"
                  />
                </div>
              </div>

              <div className="flex gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_online}
                    onChange={(e) => setForm({ ...form, is_online: e.target.checked })}
                    className="rounded text-primary"
                  />
                  <span>Online Application</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_featured}
                    onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
                    className="rounded text-primary"
                  />
                  <span>Featured Service</span>
                </label>
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
                  {createMutation.isPending ? "Creating..." : "Save Service"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
