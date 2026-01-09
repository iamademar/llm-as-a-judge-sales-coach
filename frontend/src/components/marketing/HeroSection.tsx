import Link from 'next/link';
import { Button } from '@/components/Button';
import { SectionContainer } from './ui/SectionContainer';
import {
  RiCheckLine,
  RiSparklingLine,
  RiBarChartLine,
  RiFlaskLine,
  RiShieldCheckLine,
} from '@remixicon/react';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-gray-50 dark:from-gray-950 dark:via-slate-900 dark:to-slate-800" />

      {/* Content */}
      <SectionContainer className="relative py-24 text-center">
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-slate-50">
          Turn Every Sales Call<br />
          Into Actionable Coaching
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-gray-700 dark:text-slate-300 max-w-3xl mx-auto">
          <strong>AI-powered SPIN evaluation, coaching feedback, and performance tracking</strong> — built for modern revenue teams.
        </p>

        <p className="mt-4 text-base sm:text-lg text-gray-600 dark:text-slate-400 max-w-3xl mx-auto">
          Automatically score, analyze, and coach your sales reps using the proven <strong>SPIN selling framework</strong>, powered by your choice of <strong>OpenAI, Anthropic, or Google models</strong>.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="primary" asChild className="text-base px-6 py-3">
            <Link href="/register">Get Started Free</Link>
          </Button>
          <Button variant="secondary" asChild className="text-base px-6 py-3">
            <Link href="/login">Sign In</Link>
          </Button>
        </div>

        {/* Feature Checkmarks */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-gray-700 dark:text-slate-300">
          <div className="flex items-center gap-2">
            <RiCheckLine className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Real-time AI scoring</span>
          </div>
          <div className="flex items-center gap-2">
            <RiBarChartLine className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Rep performance dashboards</span>
          </div>
          <div className="flex items-center gap-2">
            <RiFlaskLine className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Prompt & model experimentation</span>
          </div>
          <div className="flex items-center gap-2">
            <RiSparklingLine className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>LangSmith-powered evaluation</span>
          </div>
          <div className="flex items-center gap-2">
            <RiShieldCheckLine className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Secure, multi-tenant architecture</span>
          </div>
        </div>
      </SectionContainer>
    </section>
  );
}
