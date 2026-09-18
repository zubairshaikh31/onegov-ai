"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Camera, Save } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const LANGS = [{ value: "en", label: "English" }, { value: "hi", label: "हिंदी" }, { value: "mr", label: "मराठी" }];
const STATES = ["Andhra Pradesh","Assam","Bihar","Chhattisgarh","Delhi","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal"];

export default function ProfilePage() {
  const { user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ full_name: user?.full_name ?? "", phone: user?.phone ?? "", preferred_language: user?.preferred_language ?? "en", preferred_state: user?.preferred_state ?? "" });
  const handleSave = async () => { setSaving(true); await new Promise(r => setTimeout(r, 800)); setSaving(false); toast.success("Profile updated"); };
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div><h1 className="text-2xl font-bold">Profile</h1><p className="text-sm text-muted-foreground mt-1">Manage your account information</p></div>
      <div className="flex items-center gap-5">
        <div className="relative">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-3xl font-bold text-primary">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
          <button className="absolute -bottom-1.5 -right-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-secondary border border-border text-muted-foreground hover:text-foreground transition-colors"><Camera className="h-3.5 w-3.5" /></button>
        </div>
        <div>
          <p className="font-semibold">{user?.full_name}</p>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
          <div className="flex gap-2 mt-1.5">{user?.roles?.map(r => (<span key={r.name} className="rounded-md bg-primary/10 border border-primary/20 px-2 py-0.5 text-xs font-medium text-primary capitalize">{r.name}</span>))}</div>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-6 space-y-5">
        <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Personal Information</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><label className="text-sm font-medium">Full name</label><input type="text" value={form.full_name} onChange={e => setForm(f => ({...f, full_name: e.target.value}))} className="input-premium" /></div>
          <div className="space-y-1.5"><label className="text-sm font-medium">Phone</label><input type="tel" value={form.phone} placeholder="+91 98765 43210" onChange={e => setForm(f => ({...f, phone: e.target.value}))} className="input-premium" /></div>
          <div className="space-y-1.5"><label className="text-sm font-medium">Email</label><input type="email" value={user?.email ?? ""} disabled className="input-premium opacity-50 cursor-not-allowed" /></div>
          <div className="space-y-1.5"><label className="text-sm font-medium">Language</label><select value={form.preferred_language} onChange={e => setForm(f => ({...f, preferred_language: e.target.value}))} className="input-premium">{LANGS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}</select></div>
          <div className="sm:col-span-2 space-y-1.5"><label className="text-sm font-medium">Home state <span className="text-muted-foreground font-normal">(for scheme recommendations)</span></label><select value={form.preferred_state} onChange={e => setForm(f => ({...f, preferred_state: e.target.value}))} className="input-premium"><option value="">Select state…</option>{STATES.map(s => <option key={s} value={s}>{s}</option>)}</select></div>
        </div>
        <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }} onClick={handleSave} disabled={saving} className="btn-primary gap-2">
          {saving ? <><Loader2 className="h-4 w-4 animate-spin" />Saving…</> : <><Save className="h-4 w-4" />Save changes</>}
        </motion.button>
      </div>
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Security</h2>
        <div className="flex items-center justify-between">
          <div><p className="text-sm font-medium">Email verification</p><p className={cn("text-xs", user?.is_email_verified ? "text-green-500" : "text-amber-500")}>{user?.is_email_verified ? "✓ Verified" : "Not verified"}</p></div>
        </div>
        <div className="flex items-center justify-between">
          <div><p className="text-sm font-medium">Password</p><p className="text-xs text-muted-foreground">Change your login password</p></div>
          <button className="btn-secondary text-sm">Change</button>
        </div>
      </div>
    </div>
  );
}
