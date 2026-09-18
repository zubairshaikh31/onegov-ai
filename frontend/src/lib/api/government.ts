import apiClient from "./client";
import type { ApiResponse } from "@/types/auth";
import type {
  Category,
  ChatMessage,
  ChatSource,
  FAQ,
  Ministry,
  Scheme,
  SearchResult,
  Service,
  UserNotification,
} from "@/types/government";

export const governmentApi = {
  // ── Services ─────────────────────────────────────────────────────────────
  getServices: (params?: {
    q?: string;
    category_slug?: string;
    ministry_slug?: string;
    is_online?: boolean;
    is_featured?: boolean;
    sort_by?: string;
    page?: number;
    page_size?: number;
  }) =>
    apiClient
      .get<ApiResponse<{ items: Service[]; total: number; page: number; page_size: number; total_pages: number }>>(
        "/services",
        { params }
      )
      .then((r) => r.data),

  getFeaturedServices: () =>
    apiClient.get<ApiResponse<Service[]>>("/services/featured").then((r) => r.data),

  getServiceBySlug: (slug: string) =>
    apiClient.get<ApiResponse<Service>>(`/services/${slug}`).then((r) => r.data),

  // ── Schemes ──────────────────────────────────────────────────────────────
  getSchemes: (params?: {
    q?: string;
    scheme_type?: string;
    beneficiary?: string;
    ministry_slug?: string;
    is_featured?: boolean;
    page?: number;
    page_size?: number;
  }) =>
    apiClient
      .get<ApiResponse<{ items: Scheme[]; total: number; page: number; page_size: number; total_pages: number }>>(
        "/schemes",
        { params }
      )
      .then((r) => r.data),

  getFeaturedSchemes: () =>
    apiClient.get<ApiResponse<Scheme[]>>("/schemes/featured").then((r) => r.data),

  getSchemeBySlug: (slug: string) =>
    apiClient.get<ApiResponse<Scheme>>(`/schemes/${slug}`).then((r) => r.data),

  // ── Categories ───────────────────────────────────────────────────────────
  getCategories: () =>
    apiClient.get<ApiResponse<Category[]>>("/categories").then((r) => r.data),

  getCategoryBySlug: (slug: string) =>
    apiClient.get<ApiResponse<Category & { services: Service[] }>>(`/categories/${slug}`).then((r) => r.data),

  // ── Ministries ───────────────────────────────────────────────────────────
  getMinistries: () =>
    apiClient.get<ApiResponse<Ministry[]>>("/ministries").then((r) => r.data),

  getMinistryBySlug: (slug: string) =>
    apiClient.get<ApiResponse<Ministry>>(`/ministries/${slug}`).then((r) => r.data),

  // ── Search ───────────────────────────────────────────────────────────────
  search: (params: {
    q: string;
    type?: string;
    category_slug?: string;
    ministry_slug?: string;
    is_online?: boolean;
    sort_by?: string;
    page?: number;
    page_size?: number;
  }) =>
    apiClient
      .get<
        ApiResponse<{
          query: string;
          results: SearchResult[];
          total: number;
          page: number;
          page_size: number;
          total_pages: number;
        }>
      >("/search", { params })
      .then((r) => r.data),

  getSearchSuggestions: (q: string) =>
    apiClient
      .get<
        ApiResponse<{
          query: string;
          services: Array<{ name: string; slug: string; description?: string }>;
          schemes: Array<{ name: string; slug: string; beneficiary?: string }>;
          faqs: Array<{ question: string }>;
          ministries: Array<{ name: string; slug: string }>;
        }>
      >("/search/suggestions", { params: { q } })
      .then((r) => r.data),

  getPopularSearches: () =>
    apiClient
      .get<
        ApiResponse<{
          trending: string[];
          top_categories: Array<{ name: string; slug: string; icon: string }>;
        }>
      >("/search/popular")
      .then((r) => r.data),

  // ── FAQs ─────────────────────────────────────────────────────────────────
  getFaqs: (params?: { q?: string; entity_type?: string; page?: number; page_size?: number }) =>
    apiClient
      .get<ApiResponse<{ items: FAQ[]; page: number; page_size: number }>>("/faqs", { params })
      .then((r) => r.data),

  // ── Contact ──────────────────────────────────────────────────────────────
  submitContact: (body: { name: string; email: string; phone?: string; subject: string; message: string }) =>
    apiClient.post<ApiResponse<{ id: string; status: string }>>("/contact", body).then((r) => r.data),

  // ── Bookmarks ────────────────────────────────────────────────────────────
  getBookmarks: () =>
    apiClient
      .get<ApiResponse<{ services: Service[]; schemes: Scheme[]; total: number }>>("/bookmarks")
      .then((r) => r.data),

  toggleBookmark: (entity_type: "service" | "scheme", entity_id: string) =>
    apiClient
      .post<ApiResponse<{ bookmarked: boolean; entity_type: string; entity_id: string }>>("/bookmarks/toggle", {
        entity_type,
        entity_id,
      })
      .then((r) => r.data),

  // ── Notifications ────────────────────────────────────────────────────────
  getNotifications: () =>
    apiClient.get<ApiResponse<UserNotification[]>>("/notifications").then((r) => r.data),

  markNotificationRead: (id: string) =>
    apiClient.post<ApiResponse<null>>(`/notifications/${id}/read`).then((r) => r.data),

  markAllNotificationsRead: () =>
    apiClient.post<ApiResponse<null>>("/notifications/read-all").then((r) => r.data),

  // ── AI RAG Chat & Tools ──────────────────────────────────────────────────
  aiChat: (body: { message: string; session_id?: string; history?: Array<{ role: string; content: string }> }) =>
    apiClient
      .post<ApiResponse<{ content: string; sources: ChatSource[]; model: string; session_id: string }>>(
        "/ai/chat",
        body
      )
      .then((r) => r.data),

  checkEligibility: (body: {
    service_or_scheme: string;
    age?: number;
    annual_income?: number;
    state?: string;
    category?: string;
    occupation?: string;
    gender?: string;
  }) =>
    apiClient
      .post<
        ApiResponse<{
          eligible: boolean;
          confidence: number;
          summary: string;
          matching_criteria: string[];
          disqualifiers: string[];
          required_documents: string[];
          next_steps: string[];
          official_portal?: string;
        }>
      >("/ai/eligibility-check", body)
      .then((r) => r.data),

  getServiceAiSummary: (slug: string) =>
    apiClient.get<ApiResponse<{ name: string; ai_summary: string; ai_explanation: string; common_mistakes: string[]; official_url?: string }>>(
      `/ai/summary/${slug}`
    ).then((r) => r.data),

  getAiHealth: () =>
    apiClient
      .get<
        ApiResponse<{
          provider: string;
          model: string;
          ollama_available: boolean;
          database_connected: boolean;
          healthy: boolean;
          error?: string | null;
        }>
      >("/ai/health")
      .then((r) => r.data),

  getAiHistory: (params?: { session_id?: string }) =>
    apiClient.get<ApiResponse<ChatMessage[]>>("/ai/history", { params }).then((r) => r.data),


  // ── Admin ────────────────────────────────────────────────────────────────
  getAdminOverview: () =>
    apiClient.get<ApiResponse<{ stats: any; system: any }>>("/admin/overview").then((r) => r.data),

  getAdminAnalytics: () =>
    apiClient.get<ApiResponse<{ top_services: any[]; popular_searches: any[]; ai_usage: any[]; user_growth: any[] }>>(
      "/admin/analytics"
    ).then((r) => r.data),

  getAdminUsers: (params?: { q?: string; page?: number; page_size?: number }) =>
    apiClient.get<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>>("/admin/users", { params }).then((r) => r.data),

  toggleUserStatus: (userId: string) =>
    apiClient.post<ApiResponse<null>>(`/admin/users/${userId}/toggle-status`).then((r) => r.data),

  getAdminAiLogs: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<ApiResponse<{ items: any[]; total: number }>>("/admin/ai-logs", { params }).then((r) => r.data),

  getAdminFeedback: () =>
    apiClient.get<ApiResponse<{ items: any[] }>>("/admin/feedback").then((r) => r.data),

  createService: (body: any) =>
    apiClient.post<ApiResponse<any>>("/admin/services", body).then((r) => r.data),

  deleteService: (id: string) =>
    apiClient.delete<ApiResponse<null>>(`/admin/services/${id}`).then((r) => r.data),

  createScheme: (body: any) =>
    apiClient.post<ApiResponse<any>>("/admin/schemes", body).then((r) => r.data),

  deleteScheme: (id: string) =>
    apiClient.delete<ApiResponse<null>>(`/admin/schemes/${id}`).then((r) => r.data),
};
