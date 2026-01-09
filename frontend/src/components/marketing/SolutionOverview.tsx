import { RiCheckLine } from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';

const benefits = [
  'SPIN-based skill scoring',
  'Clear coaching feedback',
  'Rep performance trends',
  'Prompt & model experimentation',
  'Statistically valid AI evaluation',
];

export function SolutionOverview() {
  return (
    <section className="py-24 bg-white dark:bg-slate-900">
      <SectionContainer>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-6">
              A True AI Sales Coaching Engine<br />
              <span className="text-gray-600 dark:text-slate-400">Not Just a Call Recorder</span>
            </h2>
          </div>

          <div className="rounded-xl border border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/70 p-8">
            <p className="text-lg text-gray-700 dark:text-slate-300 mb-6">
              This platform transforms raw transcripts into:
            </p>

            <ul className="space-y-3">
              {benefits.map((benefit) => (
                <li key={benefit} className="flex items-start gap-3">
                  <RiCheckLine
                    className="size-6 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5"
                    aria-hidden="true"
                  />
                  <span className="text-base text-gray-900 dark:text-slate-50">{benefit}</span>
                </li>
              ))}
            </ul>

            <p className="text-base text-gray-600 dark:text-slate-400 mt-6">
              All inside a secure, organization-aware platform.
            </p>
          </div>
        </div>
      </SectionContainer>
    </section>
  );
}
