import {
  RiBrainLine,
  RiLightbulbLine,
  RiTeamLine,
  RiFlaskLine,
  RiBarChartLine,
  RiShieldCheckLine,
} from '@remixicon/react';
import { SectionContainer } from './ui/SectionContainer';
import { FeatureCard } from './ui/FeatureCard';

const features = [
  {
    icon: RiBrainLine,
    title: 'AI-Powered SPIN Scoring',
    description: 'Each transcript is automatically scored across Situation, Problem, Implication, Need-Payoff, Flow, Tone, and Engagement. Every score is evidence-based and stored for long-term tracking.',
  },
  {
    icon: RiLightbulbLine,
    title: 'Automated Coaching Feedback',
    description: 'Every call produces a summary of performance, key wins, identified gaps, and actionable next steps. Your reps know exactly what to improve after every call.',
  },
  {
    icon: RiTeamLine,
    title: 'Sales Rep Performance Tracking',
    description: 'Track rep leaderboards, volume vs quality trends, skill progression over time, and coaching queues. You don\'t just see performance — you manage it.',
  },
  {
    icon: RiFlaskLine,
    title: 'Prompt & Model Experimentation',
    description: 'Create multiple prompt templates, run A/B evaluations, switch between OpenAI, Anthropic, or Google models, and track how scoring quality changes per prompt + model.',
  },
  {
    icon: RiBarChartLine,
    title: 'LangSmith-Powered Evaluation',
    description: 'Upload golden datasets and measure Pearson correlation, Quadratic Weighted Kappa (QWK), ±1 accuracy, and per-dimension reliability. You don\'t just trust your AI — you validate it scientifically.',
  },
  {
    icon: RiShieldCheckLine,
    title: 'Enterprise-Grade Security',
    description: 'Encrypted API keys (Fernet), JWT authentication (access + refresh), organization-level isolation, and secure credential storage per team. Built for real production use.',
  },
];

export function FeaturesGrid() {
  return (
    <section className="py-24 bg-gray-50 dark:bg-gray-950">
      <SectionContainer>
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-slate-50 mb-4">
            Core Features
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            Everything you need to transform raw transcripts into measurable revenue skill improvement
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {features.map((feature) => (
            <FeatureCard key={feature.title} {...feature} />
          ))}
        </div>
      </SectionContainer>
    </section>
  );
}
