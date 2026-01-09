import { RiCheckLine } from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';

const comparisons = [
  { feature: 'Approach', traditional: 'Transcription only', platform: 'Full SPIN scoring' },
  { feature: 'Coaching Quality', traditional: 'Subjective coaching', platform: 'Evidence-based coaching' },
  { feature: 'Prompt Control', traditional: 'Fixed prompts', platform: 'Organization-level prompt control' },
  { feature: 'Benchmarking', traditional: 'No benchmarking', platform: 'Statistical evaluation' },
  { feature: 'Review Process', traditional: 'Human-only reviews', platform: 'Human + AI coaching' },
];

export function ComparisonTable() {
  return (
    <section className="py-24 bg-gray-50 dark:bg-gray-950">
      <SectionContainer>
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-4">
            Why This Platform Is Different
          </h2>
        </div>

        <div className="max-w-4xl mx-auto overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-gray-300 dark:border-slate-700">
                <th className="text-left p-4 text-sm font-semibold text-gray-900 dark:text-slate-50">
                  Feature
                </th>
                <th className="text-left p-4 text-sm font-semibold text-gray-600 dark:text-slate-400">
                  Traditional Tools
                </th>
                <th className="text-left p-4 text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                  This Platform
                </th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row, index) => (
                <tr
                  key={row.feature}
                  className={`border-b border-gray-200 dark:border-slate-800 ${
                    index % 2 === 0 ? 'bg-white dark:bg-slate-900/50' : 'bg-gray-50 dark:bg-slate-900/30'
                  }`}
                >
                  <td className="p-4 text-sm font-medium text-gray-900 dark:text-slate-50">
                    {row.feature}
                  </td>
                  <td className="p-4 text-sm text-gray-600 dark:text-slate-400">
                    {row.traditional}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <RiCheckLine
                        className="size-5 text-emerald-600 dark:text-emerald-400 shrink-0"
                        aria-hidden="true"
                      />
                      <span className="text-sm font-medium text-gray-900 dark:text-slate-50">
                        {row.platform}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionContainer>
    </section>
  );
}
