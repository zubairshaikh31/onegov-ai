"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import {
  Search, Mic, ArrowRight, Sparkles, Shield, Zap, Globe2, ChevronRight,
  MessageSquare, Bot, FileText, Building2, Star, CheckCircle, ArrowUpRight,
  Command,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Animation variants ────────────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};


const stagger = {
  visible: { transition: { staggerChildren: 0.08 } },
};

// ── Data ──────────────────────────────────────────────────────────────────────
const SEARCH_SUGGESTIONS = [
  "How do I apply for a passport?",
  "PM Kisan eligibility check",
  "Renew driving licence online",
  "Aadhaar address update",
  "Income certificate application",
  "Ayushman Bharat card registration",
];

const SERVICES = [
  { icon: "🛂", name: "Passport", slug: "svc-passport", tag: "MEA", color: "from-blue-500/20 to-blue-600/5" },
  { icon: "🪪", name: "Aadhaar Update", slug: "svc-aadhaar", tag: "UIDAI", color: "from-purple-500/20 to-purple-600/5" },
  { icon: "🚗", name: "Driving Licence", slug: "svc-dl", tag: "MoRTH", color: "from-amber-500/20 to-amber-600/5" },
  { icon: "💳", name: "PAN Card", slug: "svc-pan", tag: "IT Dept.", color: "from-green-500/20 to-green-600/5" },
  { icon: "🏠", name: "Ration Card", slug: "svc-ration", tag: "State Govt.", color: "from-red-500/20 to-red-600/5" },
  { icon: "📋", name: "Birth Certificate", slug: "svc-birth", tag: "Municipal", color: "from-cyan-500/20 to-cyan-600/5" },
  { icon: "💰", name: "Income Certificate", slug: "svc-income", tag: "State Govt.", color: "from-indigo-500/20 to-indigo-600/5" },
  { icon: "🎓", name: "Scholarship", slug: "svc-nsp", tag: "MoE", color: "from-pink-500/20 to-pink-600/5" },
];

const SCHEMES = [
  { name: "PM Kisan Samman Nidhi", slug: "sch-svc-pmkisan", amount: "₹6,000/yr", for: "Farmers", color: "#10B981" },
  { name: "Ayushman Bharat PM-JAY", slug: "sch-svc-pmjay", amount: "₹5L cover", for: "All families", color: "#3B82F6" },
  { name: "PM Awas Yojana", slug: "sch-0001", amount: "₹2.5L aid", for: "BPL families", color: "#8B5CF6" },
  { name: "Sukanya Samriddhi", slug: "sch-0002", amount: "8.2% p.a.", for: "Girl child", color: "#F59E0B" },
];


const STATS = [
  { value: "1,000+", label: "Government Services" },
  { value: "500+", label: "Welfare Schemes" },
  { value: "22", label: "Indian Languages" },
  { value: "10M+", label: "Citizens Helped" },
];

const FEATURES = [
  {
    icon: Bot,
    title: "AI-powered guidance",
    desc: "Ask in plain language. Get step-by-step guidance for any government process instantly.",
    gradient: "from-blue-500 to-blue-600",
  },
  {
    icon: Shield,
    title: "Eligibility checker",
    desc: "Tell us about yourself. We'll find every scheme and service you qualify for.",
    gradient: "from-purple-500 to-purple-600",
  },
  {
    icon: FileText,
    title: "Document checklist",
    desc: "Never arrive at a government office missing a document again.",
    gradient: "from-amber-500 to-amber-600",
  },
  {
    icon: Globe2,
    title: "Multilingual support",
    desc: "Available in English, Hindi, and Marathi. More languages coming soon.",
    gradient: "from-green-500 to-green-600",
  },
];

// ── Animated search placeholder ───────────────────────────────────────────────
function AnimatedPlaceholder() {
  const [index, setIndex] = useState(0);
  const [displayed, setDisplayed] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const current = SEARCH_SUGGESTIONS[index];
    const speed = isDeleting ? 30 : 60;

    const timer = setTimeout(() => {
      if (!isDeleting && displayed === current) {
        setTimeout(() => setIsDeleting(true), 1800);
        return;
      }
      if (isDeleting && displayed === "") {
        setIsDeleting(false);
        setIndex((i) => (i + 1) % SEARCH_SUGGESTIONS.length);
        return;
      }
      setDisplayed((prev) =>
        isDeleting ? prev.slice(0, -1) : current.slice(0, prev.length + 1)
      );
    }, speed);

    return () => clearTimeout(timer);
  }, [displayed, isDeleting, index]);

  return (
    <span className="text-muted-foreground">
      {displayed}
      <span className="animate-pulse">|</span>
    </span>
  );
}

// ── Floating blob ─────────────────────────────────────────────────────────────
function Blob({ className }: { className?: string }) {
  return (
    <div
      className={cn("absolute rounded-full opacity-20 blur-3xl will-change-transform", className)}
    />
  );
}

// ── Navbar ────────────────────────────────────────────────────────────────────
function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-border bg-background/80 backdrop-blur-xl"
          : "bg-transparent"
      )}
    >
      <div className="container-app flex h-14 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-base transition-all group-hover:bg-primary/20">
            🇮🇳
          </div>
          <span className="font-semibold text-foreground tracking-tight">OneGov AI</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {[
            ["Services", "/services"],
            ["Schemes", "/schemes"],
            ["AI Chat", "/ai-chat"],
            ["About", "/about"],
          ].map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground hover:bg-accent"
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link href="/login" className="btn-ghost text-sm px-3 py-1.5">
            Sign in
          </Link>
          <Link href="/register" className="btn-primary text-sm px-3 py-1.5">
            Get started
          </Link>
        </div>
      </div>
    </motion.header>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function Hero() {
  const [query, setQuery] = useState("");

  return (
    <section className="relative flex min-h-screen items-center overflow-hidden dot-grid">
      {/* Ambient blobs */}
      <Blob className="blob h-[500px] w-[500px] bg-blue-600 -top-40 -left-40" />
      <Blob className="blob h-[400px] w-[400px] bg-purple-600 top-20 -right-32 animation-delay-2000" />
      <Blob className="blob h-[350px] w-[350px] bg-amber-500 -bottom-20 left-1/3 animation-delay-4000" />

      {/* Radial gradient vignette */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.12),transparent)]" />

      <div className="container-app relative z-10 py-32 text-center">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="mx-auto max-w-4xl"
        >
          {/* Badge */}
          <motion.div variants={fadeUp} custom={0} className="mb-8 flex justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-medium text-primary">
              <Sparkles className="h-3 w-3" />
              AI-powered · 1000+ services · 22 languages
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={fadeUp}
            custom={1}
            className="mb-6 text-5xl font-bold leading-[1.1] tracking-tight sm:text-6xl md:text-7xl"
          >
            Every government{" "}
            <span className="gradient-text">service.</span>
            <br />
            One intelligent{" "}
            <span className="gradient-text">platform.</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={fadeUp}
            custom={2}
            className="mx-auto mb-12 max-w-2xl text-lg text-muted-foreground leading-relaxed"
          >
            Discover, understand, and access Central and State Government services —
            guided by AI, answered in your language, in seconds.
          </motion.p>

          {/* Search bar */}
          <motion.div variants={fadeUp} custom={3} className="mx-auto mb-6 max-w-2xl">
            <div className="gradient-border relative">
              <div className="relative flex items-center rounded-xl bg-card p-1.5 shadow-2xl">
                <Search className="ml-3 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-transparent px-3 py-2.5 text-sm text-foreground outline-none placeholder:text-transparent"
                  placeholder=" "
                  aria-label="Search government services"
                />
                {!query && (
                  <div className="pointer-events-none absolute left-10 top-1/2 -translate-y-1/2 text-sm">
                    <AnimatedPlaceholder />
                  </div>
                )}
                <div className="flex items-center gap-1.5 pr-1.5">
                  <button
                    className="rounded-lg p-2 text-muted-foreground transition-colors hover:text-foreground hover:bg-accent"
                    aria-label="Voice search"
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                  <Link
                    href={query ? `/search?q=${encodeURIComponent(query)}` : "/search"}
                    className="btn-primary rounded-lg px-4 py-2 text-sm"
                  >
                    Search
                  </Link>
                </div>
              </div>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Try:{" "}
              {["Passport", "PM Kisan", "Aadhaar"].map((s, i) => (
                <button
                  key={s}
                  onClick={() => setQuery(s)}
                  className="text-primary/70 hover:text-primary transition-colors"
                >
                  {s}
                  {i < 2 && <span className="text-muted-foreground mx-1.5">·</span>}
                </button>
              ))}
            </p>
          </motion.div>

          {/* CTA buttons */}
          <motion.div
            variants={fadeUp}
            custom={4}
            className="flex flex-wrap items-center justify-center gap-3"
          >
            <Link href="/register" className="btn-primary gap-2 px-6 py-3">
              Start for free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/ai-chat" className="btn-secondary gap-2 px-6 py-3">
              <MessageSquare className="h-4 w-4" />
              Try AI Assistant
            </Link>
          </motion.div>
        </motion.div>

        {/* Floating stats */}
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="mt-20 grid grid-cols-2 gap-4 sm:grid-cols-4 mx-auto max-w-3xl"
        >
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              variants={fadeUp}
              custom={5 + i}
              className="glass-card rounded-2xl p-4 text-center"
            >
              <p className="text-2xl font-bold text-foreground">{stat.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ── Services grid ─────────────────────────────────────────────────────────────
function ServicesSection() {
  return (
    <section className="section">
      <div className="container-app">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={stagger}
          className="mb-14 text-center"
        >
          <motion.p variants={fadeUp} className="mb-3 text-sm font-medium text-primary">
            Most accessed
          </motion.p>
          <motion.h2 variants={fadeUp} custom={1} className="text-3xl font-bold md:text-4xl">
            Popular services
          </motion.h2>
          <motion.p variants={fadeUp} custom={2} className="mt-4 text-muted-foreground max-w-xl mx-auto">
            The services millions of Indians use every year — fully guided, document-ready.
          </motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          variants={stagger}
          className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
        >
          {SERVICES.map((service, i) => (
            <motion.div key={service.name} variants={fadeUp} custom={i}>
              <Link href={`/services/${service.slug}`}>
                <div className={cn(
                  "group relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br p-5",
                  "transition-all duration-300 hover:border-primary/30 hover:shadow-card-hover hover:-translate-y-0.5",
                  service.color
                )}>
                  <div className="mb-3 text-3xl">{service.icon}</div>
                  <p className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors leading-tight">
                    {service.name}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{service.tag}</p>
                  <ArrowUpRight className="absolute right-3 top-3 h-4 w-4 text-muted-foreground/0 transition-all group-hover:text-muted-foreground/60 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        <div className="mt-10 text-center">
          <Link href="/services" className="btn-secondary gap-2">
            View all services
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}

// ── AI Preview ────────────────────────────────────────────────────────────────
function AISection() {
  const CHAT = [
    { role: "user", text: "I'm a farmer in Maharashtra. What schemes can I benefit from?" },
    { role: "assistant", text: "Based on your profile, you're eligible for **3 central schemes** and **2 Maharashtra state schemes**:\n\n• **PM Kisan Samman Nidhi** — ₹6,000/year direct to your bank account\n• **PM Fasal Bima Yojana** — Crop insurance from ₹1,500/season\n• **Maharashtra Shetkari Sahayata** — Emergency relief up to ₹50,000\n\nShall I show you how to apply for PM Kisan? It takes 15 minutes online." },
    { role: "user", text: "Yes, show me PM Kisan" },
  ];

  return (
    <section className="section bg-card/30">
      <div className="container-app">
        <div className="grid items-center gap-16 lg:grid-cols-2">
          {/* Left: copy */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.p variants={fadeUp} className="mb-3 text-sm font-medium text-primary">
              Powered by AI
            </motion.p>
            <motion.h2 variants={fadeUp} custom={1} className="mb-6 text-3xl font-bold md:text-4xl">
              Ask anything. Get answers,<br />not links.
            </motion.h2>
            <motion.p variants={fadeUp} custom={2} className="mb-8 text-muted-foreground leading-relaxed">
              Unlike official portals, OneGov AI understands what you need and guides you directly
              to the answer — in plain language, in your language.
            </motion.p>
            <motion.ul variants={stagger} className="space-y-3">
              {[
                "Eligibility check in under 60 seconds",
                "Document checklist auto-generated for your situation",
                "Step-by-step application guidance",
                "Answers in English, Hindi, and Marathi",
              ].map((item) => (
                <motion.li key={item} variants={fadeUp} className="flex items-start gap-3 text-sm text-muted-foreground">
                  <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                  {item}
                </motion.li>
              ))}
            </motion.ul>
            <motion.div variants={fadeUp} custom={6} className="mt-8">
              <Link href="/ai-chat" className="btn-primary gap-2">
                <Bot className="h-4 w-4" />
                Open AI Assistant
              </Link>
            </motion.div>
          </motion.div>

          {/* Right: chat mockup */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <div className="glass-card rounded-2xl overflow-hidden">
              {/* Titlebar */}
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10">
                    <Bot className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">OneGov AI</p>
                    <p className="text-xs text-green-500 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block" />
                      Online
                    </p>
                  </div>
                </div>
                <Sparkles className="h-4 w-4 text-muted-foreground" />
              </div>

              {/* Messages */}
              <div className="space-y-3 p-4">
                {CHAT.map((msg, i) => (
                  <div key={i} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
                    <div className={cn(
                      "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                        : "bg-secondary text-foreground rounded-tl-sm"
                    )}>
                      {msg.text.split("\n").map((line, j) => (
                        <p key={j} className={line === "" ? "h-2" : undefined}>
                          {line.replace(/\*\*(.*?)\*\*/g, (_, b) => b)}
                        </p>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="flex items-center gap-1.5 px-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce" />
                </div>
              </div>

              {/* Input */}
              <div className="border-t border-border p-3">
                <div className="flex items-center gap-2 rounded-xl bg-secondary/50 px-3 py-2">
                  <p className="flex-1 text-sm text-muted-foreground">Ask about any government service…</p>
                  <button className="rounded-lg bg-primary p-1.5">
                    <ArrowRight className="h-3.5 w-3.5 text-primary-foreground" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ── Features ──────────────────────────────────────────────────────────────────
function FeaturesSection() {
  return (
    <section className="section">
      <div className="container-app">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="mb-14 text-center"
        >
          <motion.h2 variants={fadeUp} className="text-3xl font-bold md:text-4xl">
            Built for every citizen
          </motion.h2>
          <motion.p variants={fadeUp} custom={1} className="mt-4 text-muted-foreground max-w-xl mx-auto">
            Regardless of your technical ability, language, or background — OneGov AI
            makes government accessible.
          </motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          variants={stagger}
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {FEATURES.map((feature, i) => (
            <motion.div key={feature.title} variants={fadeUp} custom={i}>
              <div className="premium-card h-full group">
                <div className={cn(
                  "mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br",
                  feature.gradient
                )}>
                  <feature.icon className="h-5 w-5 text-white" />
                </div>
                <h3 className="mb-2 font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ── Schemes ───────────────────────────────────────────────────────────────────
function SchemesSection() {
  return (
    <section className="section bg-card/30">
      <div className="container-app">
        <div className="mb-14 flex items-end justify-between">
          <div>
            <p className="mb-3 text-sm font-medium text-primary">Government welfare</p>
            <h2 className="text-3xl font-bold md:text-4xl">Featured schemes</h2>
          </div>
          <Link href="/schemes" className="hidden items-center gap-1 text-sm text-primary hover:underline sm:flex">
            View all <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SCHEMES.map((scheme, i) => (
            <motion.div
              key={scheme.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <Link href="/schemes">
                <div className="group relative overflow-hidden rounded-2xl border border-border bg-card p-5 transition-all duration-300 hover:border-primary/30 hover:shadow-card-hover hover:-translate-y-0.5">
                  <div
                    className="absolute inset-0 opacity-5 transition-opacity group-hover:opacity-10"
                    style={{ background: `radial-gradient(circle at top left, ${scheme.color}, transparent 70%)` }}
                  />
                  <div className="relative">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Central
                      </span>
                      <Star className="h-3.5 w-3.5 text-muted-foreground/40" />
                    </div>
                    <h3 className="mb-3 font-semibold text-sm leading-tight text-foreground">{scheme.name}</h3>
                    <p className="text-xl font-bold" style={{ color: scheme.color }}>{scheme.amount}</p>
                    <p className="mt-1 text-xs text-muted-foreground">For {scheme.for}</p>
                    <div className="mt-4 flex items-center gap-1 text-xs text-primary">
                      Check eligibility
                      <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── CTA ───────────────────────────────────────────────────────────────────────
function CTASection() {
  return (
    <section className="section">
      <div className="container-app">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-card to-purple-500/10 p-12 text-center"
        >
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(59,130,246,0.08),transparent)]" />
          <div className="relative">
            <h2 className="mb-4 text-3xl font-bold md:text-4xl">
              Ready to simplify your{" "}
              <span className="gradient-text">government journey</span>?
            </h2>
            <p className="mx-auto mb-8 max-w-xl text-muted-foreground">
              Join millions of Indian citizens who use OneGov AI to navigate government
              services faster, clearer, and with complete confidence.
            </p>
            <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/register" className="btn-primary gap-2 px-8 py-3">
                Create free account
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/services" className="btn-secondary gap-2 px-8 py-3">
                <Building2 className="h-4 w-4" />
                Browse services
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────
function Footer() {
  const LINKS = {
    Platform: [["Services", "/services"], ["Schemes", "/schemes"], ["AI Assistant", "/ai-chat"], ["Search", "/search"]],
    Resources: [["About", "/about"], ["Documentation", "/docs"], ["Contact", "/contact"], ["FAQ", "/faq"]],
    Legal: [["Privacy", "/privacy"], ["Terms", "/terms"], ["Cookies", "/cookies"]],
  };

  return (
    <footer className="border-t border-border bg-card/30">
      <div className="container-app py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Link href="/" className="mb-4 flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-base">
                🇮🇳
              </div>
              <span className="font-semibold">OneGov AI</span>
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
              Simplifying government services for every Indian citizen through AI.
              Not affiliated with the Government of India.
            </p>
          </div>
          {Object.entries(LINKS).map(([category, links]) => (
            <div key={category}>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {category}
              </p>
              <ul className="space-y-2">
                {links.map(([label, href]) => (
                  <li key={label}>
                    <Link href={href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} OneGov AI. Built for Digital India 🇮🇳
          </p>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Command className="h-3 w-3" />
            <span>One platform for every government service</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <ServicesSection />
      <AISection />
      <FeaturesSection />
      <SchemesSection />
      <CTASection />
      <Footer />
    </div>
  );
}
