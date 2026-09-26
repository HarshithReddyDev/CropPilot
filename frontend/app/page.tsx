"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Sprout,
  CloudSun,
  TrendingUp,
  Shield,
  ArrowRight,
  Github,
  Leaf,
} from "lucide-react";
import { Navbar } from "@/components/landing/navbar";
import { useTranslation } from "@/lib/i18n";

const GITHUB_URL = "https://github.com/HarshithReddyDev/CropPilot";

function FadeInSection({ children, className }: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const features = [
  { icon: Sprout, key: "landing.featCrop", bodyKey: "landing.featCropBody" },
  { icon: Shield, key: "landing.featDisease", bodyKey: "landing.featDiseaseBody" },
  { icon: CloudSun, key: "landing.featWeather", bodyKey: "landing.featWeatherBody" },
  { icon: TrendingUp, key: "landing.featMarket", bodyKey: "landing.featMarketBody" },
];

const stack = [
  "Next.js + TypeScript",
  "FastAPI + Python",
  "PostgreSQL + PostGIS",
  "PyTorch vision models",
  "Celery background jobs",
  "Docker Compose",
];

export default function LandingPage() {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onCtaClick={() => router.push("/dashboard")} />

      <main className="mx-auto w-full max-w-4xl px-4 sm:px-6">
        {/* Hero */}
        <section className="flex min-h-[62vh] flex-col justify-center py-24">
          <FadeInSection>
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              <Leaf className="h-3.5 w-3.5 text-primary" />
              {t("landing.badge")}
            </span>
            <h1 className="mt-5 text-4xl font-bold tracking-tight sm:text-5xl">
              CropPilot
              <span className="mt-2 block text-2xl font-semibold text-muted-foreground sm:text-3xl">
                {t("landing.tagline")}
              </span>
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
              {t("landing.heroBody")}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                onClick={() => router.push("/dashboard")}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
              >
                {t("landing.openApp")}
                <ArrowRight className="h-4 w-4 rtl:-scale-x-100" />
              </button>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
              >
                <Github className="h-4 w-4" />
                {t("landing.viewGithub")}
              </a>
            </div>
          </FadeInSection>
        </section>

        {/* Product overview */}
        <section id="features" className="scroll-mt-20 border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.featuresTitle")}</h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {features.map(({ icon: Icon, key, bodyKey }) => (
                <div
                  key={key}
                  className="rounded-xl border border-border bg-card p-5"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-3 font-semibold">{t(key)}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {t(bodyKey)}
                  </p>
                </div>
              ))}
            </div>
          </FadeInSection>
        </section>

        {/* Product screenshot */}
        <section className="border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.appTitle")}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.appBody")}
            </p>
            <figure className="mt-8 overflow-hidden rounded-xl border border-border shadow-sm">
              <img
                src="/screenshot-dashboard.png"
                alt={t("landing.appAlt")}
                className="w-full"
                loading="lazy"
              />
              <figcaption className="border-t border-border bg-muted/40 px-4 py-2 text-xs text-muted-foreground">
                {t("landing.appCaption")}
              </figcaption>
            </figure>
          </FadeInSection>
        </section>

        {/* Market Intelligence */}
        <section className="border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.marketTitle")}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.marketBody")}
            </p>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.marketSource")}
            </p>
            <Link
              href="/markets"
              className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
            >
              {t("landing.marketCta")}
              <ArrowRight className="h-4 w-4 rtl:-scale-x-100" />
            </Link>
          </FadeInSection>
        </section>

        {/* Why */}
        <section className="border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.whyTitle")}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.whyBody")}
            </p>
          </FadeInSection>
        </section>

        {/* Architecture */}
        <section id="architecture" className="scroll-mt-20 border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.archTitle")}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.archBody")}
            </p>
            <ul className="mt-6 flex flex-wrap gap-2">
              {stack.map((item) => (
                <li
                  key={item}
                  className="rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                >
                  {item}
                </li>
              ))}
            </ul>
          </FadeInSection>
        </section>

        {/* Open source */}
        <section className="border-t border-border py-14">
          <FadeInSection>
            <h2 className="text-2xl font-bold tracking-tight">{t("landing.ossTitle")}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {t("landing.ossBody")}
            </p>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-5 inline-flex items-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
            >
              <Github className="h-4 w-4" />
              {t("landing.viewGithub")}
            </a>
          </FadeInSection>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="font-semibold">CropPilot</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t("landing.footerTag")}
            </p>
          </div>
          <nav aria-label={t("landing.footerLabel")} className="flex flex-wrap gap-x-5 gap-y-2">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              GitHub
            </a>
            <a
              href={`${GITHUB_URL}/blob/main/README.md`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {t("landing.footerDocs")}
            </a>
            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {t("landing.openApp")}
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
