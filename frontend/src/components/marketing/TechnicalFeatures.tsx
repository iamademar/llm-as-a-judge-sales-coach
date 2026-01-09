import { RiCodeLine, RiCheckLine } from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';

const technicalFeatures = [
  'Multi-tenant organization isolation',
  'LLM credential management per org',
  'Prompt versioning',
  'Dataset-driven evaluation',
  'LangSmith experiment tracking',
  'FastAPI backend + Next.js frontend',
];

export function TechnicalFeatures() {
  return (
    <section className="py-24 bg-slate-900 dark:bg-slate-950">
      <SectionContainer>
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-900/30 px-4 py-2 mb-6">
            <RiCodeLine className="size-5 text-indigo-400" aria-hidden="true" />
            <span className="text-sm font-medium text-indigo-300">Built for Real AI Teams</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-50 mb-4">
            This Isn't a Demo Project<br />
            It's Infrastructure
          </h2>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Production-ready architecture with enterprise-grade security and multi-tenant support
          </p>
        </div>

        <div className="max-w-3xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {technicalFeatures.map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-4"
              >
                <RiCheckLine className="size-5 text-emerald-400 shrink-0" aria-hidden="true" />
                <span className="text-sm text-slate-200">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </SectionContainer>
    </section>
  );
}
