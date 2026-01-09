'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from "next/link"
import { useAuth } from '@/app/auth/AuthContext';
import { AuthLoadingSpinner } from '@/components/AuthLoading';
import { Button } from "@/components/Button"

type FeatureCard = {
  title: string
  description: string
  items: string[]
}

const heroHighlights = [
  "Real-time AI scoring",
  "Rep performance dashboards",
  "Prompt & model experimentation",
  "LangSmith-powered evaluation",
  "Secure, multi-tenant architecture",
]

const heroYouTubeVideoId = "dQw4w9WgXcQ"

const coreFeatures: FeatureCard[] = [
  {
    title: "🧠 AI-Powered SPIN Scoring",
    description:
      "Each transcript is automatically scored across the SPIN framework with evidence stored for long-term tracking.",
    items: [
      "Situation, Problem, Implication, Need-Payoff",
      "Flow, Tone, Engagement dimensions",
      "Evidence-backed scoring you can audit",
    ],
  },
  {
    title: "🎯 Automated Coaching Feedback",
    description:
      "Every call turns into precise guidance so reps know exactly how to improve after every conversation.",
    items: [
      "Performance summary and key wins",
      "Identified gaps with next steps",
      "Coaching queues to keep reps moving",
    ],
  },
  {
    title: "👥 Sales Rep Performance Tracking",
    description:
      "Track volume, quality, and progression for individuals and teams with dashboards built for managers.",
    items: [
      "Leaderboards with trend lines",
      "Volume vs quality insights",
      "Skill progression over time",
    ],
  },
  {
    title: "🧪 Prompt & Model Experimentation",
    description:
      "Experiment safely with prompts and models without risking production quality.",
    items: [
      "Prompt templates and versioning",
      "A/B evaluations across OpenAI, Anthropic, Google",
      "Quality tracking per prompt + model",
    ],
  },
  {
    title: "📊 LangSmith-Powered Evaluation",
    description:
      "Benchmark your AI with golden datasets and real reliability metrics.",
    items: [
      "Pearson correlation and Quadratic Weighted Kappa",
      "±1 accuracy with per-dimension reliability",
      "Dataset-driven evaluation for trustworthy models",
    ],
  },
  {
    title: "🔐 Enterprise-Grade Security",
    description:
      "Built for production with isolation, encrypted secrets, and strong authentication.",
    items: [
      "Encrypted API keys (Fernet)",
      "JWT authentication with refresh",
      "Organization-level isolation for credentials and data",
    ],
  },
]

const howItWorks = [
  "Upload a sales transcript",
  "AI evaluates using SPIN",
  "Instant coaching feedback",
  "Track rep performance",
  "Benchmark models & prompts",
  "Improve continuously with data",
]

const builtFor = [
  "Sales Leaders & Managers",
  "Revenue Operations",
  "AI Sales Tool Builders",
  "Coaching & Enablement Teams",
  "AI Product Teams running real evaluations",
]

const differentiation = [
  {
    traditional: "Transcription only",
    platform: "Full SPIN scoring with evidence",
  },
  {
    traditional: "Subjective coaching",
    platform: "Evidence-based, repeatable feedback",
  },
  {
    traditional: "Fixed prompts",
    platform: "Organization-level prompt control",
  },
  {
    traditional: "No benchmarking",
    platform: "Statistical evaluation with LangSmith",
  },
  {
    traditional: "Human-only reviews",
    platform: "Human + AI coaching that scales",
  },
]

const builtForAI = [
  "Multi-tenant organization isolation",
  "LLM credential management per org",
  "Prompt versioning and experiments",
  "Dataset-driven evaluation pipelines",
  "LangSmith experiment tracking",
  "FastAPI backend + Next.js frontend",
]

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/overview');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return <AuthLoadingSpinner />;
  }

  if (isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <div className="bg-slate-950 text-slate-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-slate-900 focus:outline-none"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex min-h-24 max-w-screen-2xl items-center justify-between px-6 py-6">
          <Link href="/" className="flex items-center gap-3" aria-label="Home">
            <div className="flex size-12 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-teal-500 text-xl font-bold text-slate-950 shadow-lg shadow-sky-500/30">
              SPIN
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">
                Sales Call AI
              </span>
              <span className="text-xl font-semibold text-white">
                Assessment & Coaching
              </span>
            </div>
          </Link>

          <nav aria-label="Primary" className="hidden items-center gap-8 md:flex">
            <a
              href="#core-features"
              className="text-base font-medium text-slate-200 transition hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="text-base font-medium text-slate-200 transition hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            >
              How it works
            </a>
            <a
              href="#security"
              className="text-base font-medium text-slate-200 transition hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            >
              Security
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Button
              asChild
              variant="ghost"
              className="h-11 px-4 text-base text-slate-100 hover:bg-white/5"
            >
              <Link href="/login">Login</Link>
            </Button>
            <Button asChild className="h-11 px-5 text-base">
              <Link href="/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="main-content">
        <section className="relative overflow-hidden border-b border-white/5">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.14),_transparent_35%),_radial-gradient(circle_at_bottom_right,_rgba(45,212,191,0.14),_transparent_40%)]" />
          <div className="mx-auto max-w-screen-2xl px-6 pb-20 pt-16 lg:flex lg:items-center lg:gap-12">
            <div className="relative z-10 max-w-2xl space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-sky-100">
                Spin-based coaching
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
                LangSmith benchmarking
              </div>
              <h1 className="text-4xl font-bold leading-tight text-white sm:text-5xl">
                Turn Every Sales Call Into Actionable Coaching
              </h1>
              <p className="max-w-2xl text-lg text-slate-200">
                AI-powered SPIN evaluation, coaching feedback, and performance tracking — built for modern revenue teams. Automatically score, analyze, and coach your sales reps using the proven SPIN selling framework, powered by your choice of OpenAI, Anthropic, or Google models.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <Button asChild className="px-5 py-3 text-base">
                  <Link href="/register">Get Started Free</Link>
                </Button>
                <Button
                  asChild
                  variant="secondary"
                  className="border-white/20 bg-white/10 px-5 py-3 text-base text-white hover:bg-white/20"
                >
                  <Link href="/register">Book a Demo</Link>
                </Button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 sm:gap-3" aria-label="Highlights">
                {heroHighlights.map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100"
                  >
                    <CheckIcon />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative z-10 mt-12 flex-1 lg:mt-0">
              <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 shadow-2xl shadow-sky-500/10">
                <div className="flex items-center justify-between px-6 pb-4 pt-6">
                  <div>
                    <p className="text-sm text-slate-300">Product walkthrough</p>
                    <p className="text-2xl font-semibold text-white">See SPIN Coaching in Action</p>
                  </div>
                  <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold uppercase text-emerald-100">
                    Video
                  </span>
                </div>

                <YouTubeEmbed
                  videoId={heroYouTubeVideoId}
                  title="SPIN Coaching walkthrough"
                />
              </div>
            </div>
          </div>
        </section>

        <section
          id="problem"
          aria-labelledby="problem-title"
          className="border-b border-white/5 bg-slate-900/40"
        >
          <div className="mx-auto grid max-w-screen-2xl gap-10 px-6 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div className="space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">
                Why this exists
              </p>
              <h2 id="problem-title" className="text-3xl font-bold text-white sm:text-4xl">
                Sales Coaching Is Broken at Scale
              </h2>
              <p className="text-lg text-slate-200">
                Managers rarely have the time to manually review every call, deliver consistent coaching, or safely test new AI prompts. Traditional call-review tools stop at transcription and rarely enforce real methodology.
              </p>
              <p className="text-lg text-slate-200">
                You needed a system that actually improves selling — not just records it.
              </p>
            </div>
            <div className="grid gap-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <h3 className="text-xl font-semibold text-white">Managers don&apos;t have time to:</h3>
                <ul className="mt-3 space-y-2 text-slate-200">
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Manually review every call
                  </li>
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Give consistent coaching
                  </li>
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Track improvement across teams
                  </li>
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Experiment safely with new AI prompts
                  </li>
                </ul>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <h3 className="text-xl font-semibold text-white">Traditional tools fall short:</h3>
                <ul className="mt-3 space-y-2 text-slate-200">
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Stop at transcription
                  </li>
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Don&apos;t enforce real sales methodology
                  </li>
                  <li className="flex items-start gap-2">
                    <DashIcon />
                    Don&apos;t support structured evaluation against a golden dataset
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section
          aria-labelledby="solution-title"
          className="border-b border-white/5 bg-slate-950"
        >
          <div className="mx-auto grid max-w-screen-2xl gap-10 px-6 py-16 lg:grid-cols-2 lg:items-center">
            <div className="space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-200">
                Solution overview
              </p>
              <h2 id="solution-title" className="text-3xl font-bold text-white sm:text-4xl">
                A True AI Sales Coaching Engine — Not Just a Call Recorder
              </h2>
              <p className="text-lg text-slate-200">
                Transform raw transcripts into SPIN-based skill scoring, clear coaching feedback, rep performance trends, prompt and model experimentation, and statistically valid AI evaluation — all inside a secure, organization-aware platform.
              </p>
              <div className="flex flex-wrap gap-3">
                <Badge label="SPIN scoring" />
                <Badge label="Coaching feedback" />
                <Badge label="Rep trends" />
                <Badge label="Prompt experiments" />
                <Badge label="LangSmith evals" />
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-950 to-sky-950 p-6 shadow-2xl shadow-sky-500/10">
              <div className="grid gap-3 text-sm text-slate-100 sm:grid-cols-2">
                <InsightCard title="SPIN-based skill scoring" body="Automated scoring with evidence for Situation, Problem, Implication, Need-Payoff." />
                <InsightCard title="Clear coaching feedback" body="Actionable next steps and gaps after every call." />
                <InsightCard title="Rep performance trends" body="Leaderboards and progress across teams and time." />
                <InsightCard title="Prompt & model experimentation" body="A/B prompts across OpenAI, Anthropic, and Google safely." />
                <InsightCard title="Statistically valid AI evaluation" body="Pearson, QWK, and ±1 accuracy with LangSmith benchmarking." />
                <InsightCard title="Secure, org-aware platform" body="Encrypted API keys, JWT auth, organization isolation." />
              </div>
            </div>
          </div>
        </section>

        <section
          id="core-features"
          aria-labelledby="features-title"
          className="border-b border-white/5 bg-slate-900/40"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-16">
            <div className="mb-8 space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">
                Core features
              </p>
              <h2 id="features-title" className="text-3xl font-bold text-white sm:text-4xl">
                Built for coaching that actually improves selling
              </h2>
            </div>
            <div className="grid gap-6 lg:grid-cols-3">
              {coreFeatures.map((feature) => (
                <article
                  key={feature.title}
                  className="flex flex-col gap-4 rounded-xl border border-white/10 bg-white/5 p-5"
                  aria-label={feature.title}
                >
                  <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                  <p className="text-sm text-slate-200">{feature.description}</p>
                  <ul className="space-y-2 text-sm text-slate-100">
                    {feature.items.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <CheckIcon />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section
          id="how-it-works"
          aria-labelledby="how-title"
          className="border-b border-white/5 bg-slate-950"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-16">
            <div className="mb-8 space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-200">
                How it works
              </p>
              <h2 id="how-title" className="text-3xl font-bold text-white sm:text-4xl">
                Start coaching with data, not gut feel
              </h2>
              <p className="text-lg text-slate-200">
                Upload a transcript, get SPIN scoring and coaching instantly, then benchmark prompts and models to keep quality high.
              </p>
            </div>
            <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {howItWorks.map((step, index) => (
                <li
                  key={step}
                  className="group relative overflow-hidden rounded-xl border border-white/10 bg-white/5 p-5"
                >
                  <div className="mb-3 inline-flex size-10 items-center justify-center rounded-full bg-sky-500/15 text-base font-semibold text-sky-100">
                    {index + 1}
                  </div>
                  <p className="text-lg font-semibold text-white">{step}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section
          id="why-different"
          aria-labelledby="why-title"
          className="border-b border-white/5 bg-slate-900/40"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-16">
            <div className="mb-8 space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">
                Why this platform
              </p>
              <h2 id="why-title" className="text-3xl font-bold text-white sm:text-4xl">
                Built for teams that need real improvement, not more recordings
              </h2>
            </div>
            <div className="overflow-hidden rounded-xl border border-white/10">
              <div className="grid grid-cols-2 bg-white/5 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-slate-200 sm:px-6">
                <span>Traditional tools</span>
                <span>This platform</span>
              </div>
              <div className="divide-y divide-white/10 bg-slate-950/40">
                {differentiation.map((row) => (
                  <div key={row.platform} className="grid grid-cols-1 gap-4 px-4 py-4 sm:grid-cols-2 sm:px-6">
                    <span className="text-slate-200">{row.traditional}</span>
                    <span className="font-semibold text-white">{row.platform}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="security"
          aria-labelledby="security-title"
          className="border-b border-white/5 bg-slate-950"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-16">
            <div className="mb-8 space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-200">
                Built for real AI teams
              </p>
              <h2 id="security-title" className="text-3xl font-bold text-white sm:text-4xl">
                Enterprise-grade security and architecture
              </h2>
              <p className="text-lg text-slate-200">
                Multi-tenant isolation, encrypted credentials, and evaluation pipelines that mirror the way real teams ship AI.
              </p>
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-xl border border-white/10 bg-white/5 p-5">
                <h3 className="text-xl font-semibold text-white">Security</h3>
                <ul className="mt-3 space-y-2 text-slate-100">
                  <li className="flex items-start gap-2">
                    <CheckIcon />
                    Encrypted API keys (Fernet)
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckIcon />
                    JWT authentication (access + refresh)
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckIcon />
                    Organization-level isolation for data and credentials
                  </li>
                </ul>
              </article>
              <article className="rounded-xl border border-white/10 bg-white/5 p-5">
                <h3 className="text-xl font-semibold text-white">For AI platform teams</h3>
                <ul className="mt-3 space-y-2 text-slate-100">
                  {builtForAI.map((item) => (
                    <li key={item} className="flex items-start gap-2">
                      <CheckIcon />
                      {item}
                    </li>
                  ))}
                </ul>
              </article>
            </div>
          </div>
        </section>

        <section
          aria-labelledby="audience-title"
          className="border-b border-white/5 bg-slate-900/40"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-14">
            <div className="mb-6 space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">
                Who it is for
              </p>
              <h2 id="audience-title" className="text-3xl font-bold text-white sm:text-4xl">
                Built for modern revenue and AI teams
              </h2>
            </div>
            <div className="flex flex-wrap gap-3">
              {builtFor.map((item) => (
                <Badge key={item} label={item} />
              ))}
            </div>
          </div>
        </section>

        <section
          aria-labelledby="cta-title"
          className="bg-gradient-to-br from-sky-600 via-sky-700 to-slate-950"
        >
          <div className="mx-auto max-w-screen-2xl px-6 py-16 text-center">
            <h2 id="cta-title" className="text-3xl font-bold text-white sm:text-4xl">
              Start Coaching With Data — Not Gut Feel
            </h2>
            <p className="mt-4 text-lg text-sky-50">
              Transform transcripts into measurable revenue skill improvement with SPIN-based scoring, coaching, and LangSmith evaluation.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Button asChild className="px-6 py-3 text-base">
                <Link href="/register">Create Your Workspace</Link>
              </Button>
              <Button
                asChild
                variant="secondary"
                className="border-white/30 bg-white/10 px-6 py-3 text-base text-white hover:bg-white/20"
              >
                <Link href="/register">Book a Demo</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

function CheckIcon() {
  return (
    <span
      aria-hidden="true"
      className="mt-0.5 inline-flex size-4 items-center justify-center rounded-full bg-emerald-500/20 text-[10px] font-bold text-emerald-200"
    >
      ✓
    </span>
  )
}

function DashIcon() {
  return (
    <span
      aria-hidden="true"
      className="mt-1 inline-flex h-2 w-3 shrink-0 rounded-full bg-slate-400"
    />
  )
}

function Badge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-100">
      {label}
    </span>
  )
}

function InsightCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-slate-900/60 p-4">
      <p className="text-sm font-semibold text-white">{title}</p>
      <p className="mt-1 text-sm text-slate-200">{body}</p>
    </div>
  )
}

function YouTubeEmbed({ videoId, title }: { videoId: string; title: string }) {
  return (
    <div className="relative w-full bg-black pt-[56.25%]">
      <iframe
        className="absolute inset-0 h-full w-full"
        src={`https://www.youtube-nocookie.com/embed/${videoId}?rel=0`}
        title={title}
        loading="lazy"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        referrerPolicy="strict-origin-when-cross-origin"
        allowFullScreen
      />
    </div>
  )
}
