import { RiTimeLine, RiRepeatLine, RiScalesLine, RiToolsLine } from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';

const problems = [
  {
    icon: RiTimeLine,
    title: 'No Time for Manual Review',
    description: 'Managers don\'t have time to manually review every call and give consistent coaching across teams.',
  },
  {
    icon: RiRepeatLine,
    title: 'Inconsistent Coaching',
    description: 'Traditional tools stop at transcription and don\'t enforce real sales methodology.',
  },
  {
    icon: RiScalesLine,
    title: 'No Improvement Tracking',
    description: 'Hard to track improvement across teams and experiment safely with new AI prompts.',
  },
  {
    icon: RiToolsLine,
    title: 'Lack of Structured Evaluation',
    description: 'Traditional call-review tools don\'t support structured evaluation against a golden dataset.',
  },
];

export function ProblemStatement() {
  return (
    <section className="py-24 bg-white dark:bg-slate-900">
      <SectionContainer>
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-4">
            Sales Coaching Is Broken at Scale
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            You needed a system that actually improves selling — not just records it.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {problems.map((problem) => (
            <div
              key={problem.title}
              className="rounded-xl border border-slate-800 bg-slate-900/70 dark:bg-slate-900/90 p-6"
            >
              <div className="flex items-start gap-4">
                <div className="shrink-0 rounded-lg bg-rose-900/30 p-3 text-rose-400">
                  <problem.icon className="size-6" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-50 mb-2">
                    {problem.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {problem.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </SectionContainer>
    </section>
  );
}
