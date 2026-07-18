"use client";

import { useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Sprout,
  CloudSun,
  TrendingUp,
  Landmark as Government,
  Search,
  BarChart3,
  ArrowRight,
  Play,
  Star,
  Github,
  ChevronRight,
  Leaf,
  Shield,
  Cpu,
  Database,
  LineChart,
  Smartphone,
} from "lucide-react";
import { Navbar } from "@/components/landing/navbar";
import { useAuth } from "@/hooks/use-auth";

function FadeInSection({ children, className, delay = 0 }: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const features = [
  {
    icon: Search,
    title: "Crop Health AI",
    description: "Real-time crop health monitoring using satellite imagery and AI-powered analysis to detect issues before they spread.",
    color: "from-emerald-500 to-green-600",
  },
  {
    icon: CloudSun,
    title: "Weather Intelligence",
    description: "Hyper-local weather forecasts with 7-day predictions, historical patterns, and crop-specific alerts.",
    color: "from-blue-500 to-cyan-600",
  },
  {
    icon: TrendingUp,
    title: "Market Insights",
    description: "Live commodity prices across mandis with price trends, demand forecasts, and optimal selling recommendations.",
    color: "from-amber-500 to-orange-600",
  },
  {
    icon: Government,
    title: "Scheme Advisor",
    description: "AI-matched government schemes and subsidies personalized to your farm profile and location.",
    color: "from-violet-500 to-purple-600",
  },
  {
    icon: Shield,
    title: "Disease Detection",
    description: "Upload crop photos for instant disease identification with treatment recommendations and severity assessment.",
    color: "from-rose-500 to-pink-600",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    description: "Comprehensive farm analytics with yield predictions, resource optimization, and historical comparisons.",
    color: "from-teal-500 to-emerald-600",
  },
];

const team = [
  { name: "Harsh Raj", role: "Founder & CEO", avatar: "HR" },
  { name: "Priya Sharma", role: "Head of AI", avatar: "PS" },
  { name: "Arjun Patel", role: "Lead Engineer", avatar: "AP" },
  { name: "Neha Gupta", role: "Product Designer", avatar: "NG" },
];

const techBadges = [
  "Next.js", "TypeScript", "Python", "TensorFlow", "PostgreSQL",
  "React", "TailwindCSS", "FastAPI", "Docker", "Mapbox",
];

export default function LandingPage() {
  const router = useRouter();
  const { enableDemoMode } = useAuth();
  const [email, setEmail] = useState("");

  const scrollToFeatures = () => {
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
  };

  const handleLaunchDemo = () => {
    enableDemoMode();
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onCtaClick={scrollToFeatures} />

      {/* Hero */}
      <section className="relative flex min-h-screen items-center overflow-hidden pt-16">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/10 dark:from-primary/10 dark:via-background dark:to-primary/5" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.08),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.05),transparent_50%)]" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
                  <Leaf className="h-4 w-4" />
                  AI-Powered Agriculture
                </span>
                <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl text-foreground">
                  Intelligent Agriculture{" "}
                  <span className="bg-gradient-to-r from-primary to-emerald-400 bg-clip-text text-transparent">
                    for Tomorrow
                  </span>
                </h1>
                <p className="mt-6 max-w-lg text-lg leading-relaxed text-muted-foreground">
                  Empower your farming with real-time crop health monitoring, disease detection,
                  weather intelligence, and market insights — all powered by cutting-edge AI.
                </p>
                <div className="mt-8 flex flex-wrap gap-4">
                  <button
                    onClick={scrollToFeatures}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30 active:scale-95"
                  >
                    Get Started
                    <ArrowRight className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleLaunchDemo}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:bg-emerald-600 hover:shadow-xl hover:shadow-emerald-500/30 active:scale-95"
                  >
                    <Play className="h-4 w-4" />
                    Launch Demo &rarr;
                  </button>
                </div>
                <div className="mt-8 flex items-center gap-6 text-sm text-muted-foreground">
                  <div className="flex -space-x-2">
                    {["/avatar-1.jpg", "/avatar-2.jpg", "/avatar-3.jpg"].map((src, i) => (
                      <div
                        key={i}
                        className="h-8 w-8 rounded-full border-2 border-background bg-gradient-to-br from-primary to-emerald-400 flex items-center justify-center text-[10px] font-bold text-white"
                      >
                        {"FA"[i]}
                      </div>
                    ))}
                  </div>
                  <span>
                    Trusted by <strong className="text-foreground">500+</strong> farmers
                  </span>
                </div>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              <div className="relative rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-2 shadow-2xl">
                <div className="rounded-xl bg-gradient-to-br from-muted to-background overflow-hidden">
                  <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                    <div className="flex gap-1.5">
                      <div className="h-3 w-3 rounded-full bg-red-500" />
                      <div className="h-3 w-3 rounded-full bg-amber-500" />
                      <div className="h-3 w-3 rounded-full bg-emerald-500" />
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">croppilot.app/dashboard</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 p-4">
                    {["Rice", "Wheat", "Cotton"].map((crop) => (
                      <div key={crop} className="rounded-lg bg-muted/50 p-3">
                        <div className="mb-2 h-16 rounded-md bg-gradient-to-br from-primary/20 to-primary/5" />
                        <p className="text-xs font-medium">{crop}</p>
                        <p className="text-[10px] text-muted-foreground">Health: 85%</p>
                      </div>
                    ))}
                  </div>
                  <div className="border-t border-border p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">Yield Prediction</span>
                      <span className="text-xs text-emerald-500 font-semibold">+12.5%</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
                      <div className="h-full w-3/4 rounded-full bg-gradient-to-r from-primary to-emerald-400" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-6 -left-6 rounded-xl border border-border/50 bg-card p-4 shadow-lg">
                <div className="flex items-center gap-3">
                  <CloudSun className="h-8 w-8 text-primary" />
                  <div>
                    <p className="text-xs text-muted-foreground">Weather</p>
                    <p className="text-lg font-bold">28°C</p>
                  </div>
                </div>
              </div>
              <div className="absolute -right-4 -top-4 rounded-xl border border-border/50 bg-card p-3 shadow-lg">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-emerald-500" />
                  <div className="text-right">
                    <p className="text-[10px] text-muted-foreground">Market</p>
                    <p className="text-sm font-bold">₹2,450</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInSection className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              Features
            </span>
            <h2 className="mt-4 text-3xl font-bold sm:text-4xl text-foreground">
              Everything You Need to Succeed
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              From disease detection to market insights, CropPilot provides a complete toolkit for modern farmers.
            </p>
          </FadeInSection>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description, color }, i) => (
              <FadeInSection key={title} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -6, scale: 1.01 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="group relative overflow-hidden rounded-2xl border border-border/50 bg-card p-6 transition-shadow hover:shadow-xl hover:shadow-primary/5"
                >
                  <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${color} text-white shadow-lg`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
                  <div className="mt-4 flex items-center gap-1 text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
                    Learn more <ChevronRight className="h-3.5 w-3.5" />
                  </div>
                </motion.div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="relative py-24 bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInSection className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              Architecture
            </span>
            <h2 className="mt-4 text-3xl font-bold sm:text-4xl text-foreground">
              How CropPilot Works
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              A modern, scalable architecture connecting edge devices to AI-powered insights.
            </p>
          </FadeInSection>

          <FadeInSection className="mt-16">
            <div className="relative">
              <div className="absolute left-0 right-0 top-1/2 hidden h-0.5 bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0 lg:block" />
              <div className="grid gap-8 lg:grid-cols-4">
                {[
                  { icon: Smartphone, title: "Edge Devices", desc: "Farm sensors, drones, and mobile capture", color: "from-blue-500 to-cyan-600" },
                  { icon: Database, title: "API Layer", desc: "REST & WebSocket APIs for real-time data", color: "from-violet-500 to-purple-600" },
                  { icon: Cpu, title: "AI Engine", desc: "TensorFlow models for detection & prediction", color: "from-amber-500 to-orange-600" },
                  { icon: LineChart, title: "Dashboard", desc: "Interactive analytics and farm management", color: "from-emerald-500 to-green-600" },
                ].map(({ icon: Icon, title, desc, color }, i) => (
                  <motion.div
                    key={title}
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.15 }}
                    className="relative flex flex-col items-center text-center"
                  >
                    <div className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${color} text-white shadow-lg mb-4`}>
                      <Icon className="h-8 w-8" />
                    </div>
                    <div className="rounded-xl border border-border/50 bg-card p-4 w-full">
                      <h3 className="font-semibold text-foreground">{title}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
                    </div>
                    {i < 3 && (
                      <div className="hidden lg:block absolute -right-4 top-8 text-primary/40">
                        <ArrowRight className="h-6 w-6" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Demo */}
      <section id="demo" className="relative py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInSection className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              Demo
            </span>
            <h2 className="mt-4 text-3xl font-bold sm:text-4xl text-foreground">
              See CropPilot in Action
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              Watch how our platform transforms agricultural data into actionable insights.
            </p>
          </FadeInSection>

          <FadeInSection className="mt-12">
            <div className="group relative mx-auto max-w-4xl overflow-hidden rounded-2xl border border-border/50 bg-card shadow-2xl">
              <div className="aspect-video bg-gradient-to-br from-muted to-background flex items-center justify-center">
                <div className="relative">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex h-20 w-20 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-xl shadow-primary/30 transition-all hover:shadow-2xl hover:shadow-primary/40"
                  >
                    <Play className="h-8 w-8 ml-1" />
                  </motion.button>
                  <div className="absolute -inset-4 rounded-full bg-primary/20 animate-ping" />
                </div>
              </div>
              <div className="absolute bottom-4 left-4 right-4 flex justify-center gap-4">
                {[
                  { label: "Active Users", value: "500+" },
                  { label: "Crops Analyzed", value: "50K+" },
                  { label: "Diseases Detected", value: "98.5%" },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-lg bg-background/90 backdrop-blur-sm border border-border/50 px-4 py-2 text-center">
                    <p className="text-lg font-bold text-foreground">{value}</p>
                    <p className="text-[10px] text-muted-foreground">{label}</p>
                  </div>
                ))}
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* GitHub */}
      <section className="relative py-24 bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInSection className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              <Github className="h-4 w-4" />
              Open Source
            </div>
            <h2 className="mt-4 text-3xl font-bold sm:text-4xl text-foreground">
              Built in the Open
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              CropPilot is open source. Contribute, fork, or use it for your own projects.
            </p>
          </FadeInSection>

          <FadeInSection className="mt-10" delay={0.1}>
            <div className="mx-auto max-w-md rounded-2xl border border-border/50 bg-card p-8 text-center shadow-xl">
              <div className="flex items-center justify-center gap-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="h-5 w-5 fill-amber-400 text-amber-400" />
                ))}
              </div>
              <p className="mt-3 text-4xl font-bold text-foreground">1.2K</p>
              <p className="text-sm text-muted-foreground">GitHub Stars</p>
              <a
                href="https://github.com/anomalyco/CropPilot"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-foreground px-6 py-3 text-sm font-semibold text-background transition-all hover:bg-foreground/90 active:scale-95"
              >
                <Github className="h-5 w-5" />
                View on GitHub
              </a>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {techBadges.map((badge) => (
                  <span
                    key={badge}
                    className="rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Team */}
      <section id="team" className="relative py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInSection className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              Team
            </span>
            <h2 className="mt-4 text-3xl font-bold sm:text-4xl text-foreground">
              Meet the Founders
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              A passionate team building the future of agriculture technology.
            </p>
          </FadeInSection>

          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {team.map(({ name, role, avatar }, i) => (
              <FadeInSection key={name} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="group rounded-2xl border border-border/50 bg-card p-6 text-center transition-shadow hover:shadow-xl"
                >
                  <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-primary to-emerald-400 text-xl font-bold text-white shadow-lg">
                    {avatar}
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-foreground">{name}</h3>
                  <p className="text-sm text-muted-foreground">{role}</p>
                  <div className="mt-4 flex justify-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                    {["Twitter", "LinkedIn", "GitHub"].map((s) => (
                      <span
                        key={s}
                        className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </motion.div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.08),transparent_60%)]" />

        <FadeInSection className="relative mx-auto max-w-2xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold sm:text-4xl text-foreground">
            Ready to Transform Your Farming?
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join thousands of farmers using CropPilot to increase yields and reduce costs.
          </p>
          <form
            onSubmit={(e) => { e.preventDefault(); }}
            className="mx-auto mt-8 flex max-w-md gap-3"
          >
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none ring-1 ring-transparent transition-all focus:ring-primary"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl active:scale-95"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </FadeInSection>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Sprout className="h-4 w-4" />
                </div>
                <span className="text-lg font-bold text-foreground">CropPilot</span>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">
                Intelligent agriculture platform powered by AI.
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-foreground">Product</h4>
              <ul className="mt-4 space-y-2">
                {["Features", "Pricing", "Demo", "Changelog"].map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground">Company</h4>
              <ul className="mt-4 space-y-2">
                {["About", "Blog", "Careers", "Contact"].map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground">Legal</h4>
              <ul className="mt-4 space-y-2">
                {["Privacy", "Terms", "Security", "Cookies"].map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} CropPilot. All rights reserved.
            </p>
            <div className="flex gap-4">
              {["Twitter", "GitHub", "LinkedIn", "YouTube"].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {social}
                </a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
