export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  icon?: string | null;
  image_url?: string | null;
  display_order?: number;
  services_count?: number;
}

export interface Ministry {
  id: string;
  name: string;
  slug: string;
  short_name?: string | null;
  description?: string | null;
  ministry_type?: string;
  state_name?: string | null;
  website?: string | null;
  logo_url?: string | null;
  departments_count?: number;
  departments?: Department[];
}

export interface Department {
  id: string;
  ministry_id: string;
  name: string;
  slug: string;
  description?: string | null;
  website?: string | null;
  ministry?: Ministry | null;
}

export interface RequiredDocument {
  id: string;
  name: string;
  description?: string | null;
  is_mandatory?: boolean;
  notes?: string | null;
  example_url?: string | null;
}

export interface ApplicationStep {
  step_number: number;
  title: string;
  description?: string | null;
  step_type?: string;
  action_url?: string | null;
  estimated_time?: string | null;
}

export interface FAQ {
  id: string;
  question: string;
  answer: string;
  entity_type?: string;
}

export interface Service {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  short_description?: string | null;
  sub_category?: string | null;
  government_level?: string | null;
  state_id?: string | null;
  eligibility_description?: string | null;
  benefits?: string | null;
  fee_description?: string | null;
  fee_amount?: number | null;
  processing_time?: string | null;
  validity?: string | null;
  official_url?: string | null;
  official_apply_link?: string | null;
  helpline_number?: string | null;
  email?: string | null;
  is_online: boolean;
  is_offline: boolean;
  is_active: boolean;
  is_featured: boolean;
  view_count: number;
  bookmark_count: number;
  tags?: string[] | null;
  category?: Category | null;
  department?: Department | null;
  ministry?: Ministry | null;
  documents?: RequiredDocument[];
  application_steps?: ApplicationStep[];
  faqs?: FAQ[];
  related_services?: Array<{ name: string; slug: string; description?: string }>;
  related_schemes?: Scheme[];
  videos?: Array<{
    id: string;
    youtube_video_id: string;
    youtube_url: string;
    title: string;
    channel_name?: string | null;
    description?: string | null;
    thumbnail_url?: string | null;
  }>;
  is_bookmarked?: boolean;
  ai_summary?: string | null;
  ai_explanation?: string | null;
}

export interface Scheme {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  short_description?: string | null;
  scheme_type: string;
  government_level?: string | null;
  state_name?: string | null;
  target_beneficiary?: string | null;
  eligibility_description?: string | null;
  benefits_description?: string | null;
  benefit_amount?: string | null;
  application_deadline?: string | null;
  official_url?: string | null;
  official_portal?: string | null;
  is_active: boolean;
  is_featured: boolean;
  tags?: string[] | null;
  ministry?: Ministry | null;
  service?: Service | null;
  faqs?: FAQ[];
  is_bookmarked?: boolean;
}

export interface SearchResult {
  type: "service" | "scheme" | "faq" | "ministry";
  id: string;
  name?: string;
  slug?: string;
  description?: string;
  question?: string;
  answer?: string;
  category?: string;
  category_slug?: string;
  department?: string;
  ministry?: string;
  target_beneficiary?: string;
  benefit_amount?: string;
  official_url?: string;
  url: string;
  is_online?: boolean;
  fee_description?: string;
  processing_time?: string;
}

export interface ChatSource {
  title: string;
  type: string;
  slug: string;
  url: string;
  confidence?: number;
}

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  sources?: ChatSource[];
  loading?: boolean;
};


export interface UserNotification {
  id: string;
  title: string;
  message: string;
  notification_type: "info" | "success" | "warning" | "error";
  is_read: boolean;
  created_at: string;
  action_url?: string | null;
}
