"use client";
import { useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor, Bell, Shield, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!checked)} className={cn("relative inline-flex h-5 w-9 items-center rounded-full border transition-colors", checked ? "bg-primary border-primary" : "bg-secondary border-border")}>
      <span className={cn("inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform", checked ? "translate-x-4" : "translate-x-0.5")} />
    </button>
  );
}

const THEMES = [{ value: "dark", label: "Dark", icon: Moon }, { value: "light", label: "Light", icon: Sun }, { value: "system", label: "System", icon: Monitor }];

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [notifs, setNotifs] = useState({ email: true, push: false, schemes: true });
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div><h1 className="text-2xl font-bold">Settings</h1><p className="text-sm text-muted-foreground mt-1">Manage your preferences</p></div>
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2"><Monitor className="h-4 w-4 text-muted-foreground" /><h2 className="font-semibold text-sm">Appearance</h2></div>
        <div className="grid grid-cols-3 gap-2">
          {THEMES.map(({ value, label, icon: Icon }) => (
            <button key={value} onClick={() => setTheme(value)} className={cn("flex flex-col items-center gap-2 rounded-xl border p-3 text-sm transition-all", theme === value ? "border-primary bg-primary/10 text-primary" : "border-border bg-secondary/30 text-muted-foreground hover:border-primary/30 hover:text-foreground")}>
              <Icon className="h-4 w-4" />{label}
            </button>
          ))}
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2"><Bell className="h-4 w-4 text-muted-foreground" /><h2 className="font-semibold text-sm">Notifications</h2></div>
        {[
          { key: "email", label: "Email notifications", desc: "Updates about bookmarked services" },
          { key: "push", label: "Push notifications", desc: "Browser push for important alerts" },
          { key: "schemes", label: "New scheme alerts", desc: "Notify when new schemes launch" },
        ].map(({ key, label, desc }) => (
          <div key={key} className="flex items-center justify-between">
            <div><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{desc}</p></div>
            <Toggle checked={notifs[key as keyof typeof notifs]} onChange={v => setNotifs(n => ({...n, [key]: v}))} />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 space-y-4">
        <div className="flex items-center gap-2"><Shield className="h-4 w-4 text-destructive" /><h2 className="font-semibold text-sm text-destructive">Danger zone</h2></div>
        <div className="flex items-center justify-between">
          <div><p className="text-sm font-medium">Delete account</p><p className="text-xs text-muted-foreground">Permanently delete your account and all data</p></div>
          <button onClick={() => toast.error("Contact support to delete your account")} className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive hover:bg-destructive/20 transition-all">
            <Trash2 className="h-3.5 w-3.5" />Delete
          </button>
        </div>
      </div>
    </div>
  );
}
