import { SectionContainer } from './ui/SectionContainer';

const steps = [
  { number: 1, title: 'Upload a sales transcript', description: 'Import your call transcripts from any source' },
  { number: 2, title: 'AI evaluates using SPIN', description: 'Our AI analyzes the conversation using the proven SPIN framework' },
  { number: 3, title: 'Instant coaching feedback', description: 'Receive detailed, actionable coaching insights immediately' },
  { number: 4, title: 'Track rep performance', description: 'Monitor individual and team performance over time' },
  { number: 5, title: 'Benchmark models & prompts', description: 'Test and optimize different AI models and prompts' },
  { number: 6, title: 'Improve continuously with data', description: 'Use scientific evaluation metrics to drive improvement' },
];

export function HowItWorks() {
  return (
    <section className="py-24 bg-white dark:bg-slate-900">
      <SectionContainer>
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-4">
            How It Works
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {steps.map((step) => (
            <div key={step.number} className="relative">
              {/* Step Card */}
              <div className="rounded-xl border border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/70 p-6 h-full">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 flex items-center justify-center size-10 rounded-full bg-indigo-600 dark:bg-indigo-500 text-white font-bold text-lg">
                    {step.number}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-50 mb-2">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-slate-400">
                      {step.description}
                    </p>
                  </div>
                </div>
              </div>

              {/* Connector (hidden on mobile, shown on desktop for non-last items in row) */}
              {step.number < steps.length && (
                <div
                  className={`hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-indigo-300 to-transparent dark:from-indigo-700 ${
                    step.number % 3 === 0 ? 'lg:hidden' : ''
                  }`}
                  aria-hidden="true"
                />
              )}
            </div>
          ))}
        </div>
      </SectionContainer>
    </section>
  );
}
