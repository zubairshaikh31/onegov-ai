"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, TrendingUp, Users, Search, Bot } from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, PieChart, Pie, Cell,
} from "recharts";
import { governmentApi } from "@/lib/api/government";

const COLORS = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444", "#EC4899"];

export default function AdminAnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-analytics"],
    queryFn: () => governmentApi.getAdminAnalytics(),
  });

  const analytics = data?.data;
  const userGrowth = analytics?.user_growth || [
    { month: "Jan", users: 120 },
    { month: "Feb", users: 280 },
    { month: "Mar", users: 490 },
    { month: "Apr", users: 730 },
    { month: "May", users: 1050 },
    { month: "Jun", users: 1420 },
  ];

  const aiUsage = analytics?.ai_usage || [
    { day: "Mon", queries: 340, tokens: 42000 },
    { day: "Tue", queries: 420, tokens: 51000 },
    { day: "Wed", queries: 510, tokens: 63000 },
    { day: "Thu", queries: 480, tokens: 59000 },
    { day: "Fri", queries: 620, tokens: 78000 },
    { day: "Sat", queries: 530, tokens: 64000 },
    { day: "Sun", queries: 390, tokens: 47000 },
  ];

  const popularSearches = analytics?.popular_searches || [
    { name: "Passport Seva", searches: 1420 },
    { name: "Aadhaar Update", searches: 1280 },
    { name: "PM Kisan", searches: 980 },
    { name: "Ayushman Bharat", searches: 870 },
    { name: "Driving Licence", searches: 740 },
    { name: "PAN Card", searches: 690 },
  ];

  const topServices = analytics?.top_services || [
    { name: "Passport", views: 4200 },
    { name: "Aadhaar", views: 3800 },
    { name: "PM Kisan", views: 2900 },
    { name: "Driving Licence", views: 2400 },
    { name: "PAN Card", views: 2100 },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
          Platform Analytics & Usage
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Deep telemetry on citizen search queries, AI interactions, service pageviews, and account registrations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">User Growth Over Time</h2>
              <p className="text-xs text-muted-foreground">Monthly registered citizen accounts</p>
            </div>
            <Users className="h-5 w-5 text-primary" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={userGrowth}>
                <defs>
                  <linearGradient id="userGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="month" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#18181b", borderRadius: "12px", border: "1px solid #27272a", fontSize: "12px" }} />
                <Area type="monotone" dataKey="users" stroke="#3B82F6" strokeWidth={2.5} fill="url(#userGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Queries Chart */}
        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">AI Daily Queries</h2>
              <p className="text-xs text-muted-foreground">Conversational consultations per day</p>
            </div>
            <Bot className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={aiUsage}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="day" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#18181b", borderRadius: "12px", border: "1px solid #27272a", fontSize: "12px" }} />
                <Bar dataKey="queries" fill="#10B981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Search Queries */}
        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Popular Search Keywords</h2>
              <p className="text-xs text-muted-foreground">Most frequent citizen searches</p>
            </div>
            <Search className="h-5 w-5 text-amber-500" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={popularSearches}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis type="number" fontSize={11} tickLine={false} />
                <YAxis dataKey="name" type="category" fontSize={10} width={90} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#18181b", borderRadius: "12px", border: "1px solid #27272a", fontSize: "12px" }} />
                <Bar dataKey="searches" fill="#F59E0B" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Services Viewed */}
        <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Top Service Pageviews</h2>
              <p className="text-xs text-muted-foreground">Most accessed service guides</p>
            </div>
            <TrendingUp className="h-5 w-5 text-purple-500" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topServices}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="name" fontSize={10} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#18181b", borderRadius: "12px", border: "1px solid #27272a", fontSize: "12px" }} />
                <Bar dataKey="views" fill="#8B5CF6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
