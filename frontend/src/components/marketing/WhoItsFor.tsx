import { RiCheckLine } from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';

const audiences = [
  'Sales Leaders & Managers',
  'Revenue Operations',
  'AI Sales Tool Builders',
  'Coaching & Enablement Teams',
  'AI Product Teams running real evaluations',
];

export function WhoItsFor() {
  return (
    <section className="py-24 bg-gray-50 dark:bg-gray-950">
      <SectionContainer>
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-4">
            Who It's For
          </h2>
        </div>

        <div className="max-w-2xl mx-auto">
          <div className="rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 p-8 shadow-sm">
            <ul className="space-y-4">
              {audiences.map((audience) => (
                <li key={audience} className="flex items-start gap-3">
                  <RiCheckLine
                    className="size-6 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5"
                    aria-hidden="true"
                  />
                  <span className="text-lg text-gray-900 dark:text-slate-50">{audience}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </SectionContainer>
    </section>
  );
}
