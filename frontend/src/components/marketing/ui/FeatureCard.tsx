import React from 'react';

interface FeatureCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
}

export function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <div className="group rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 p-6 shadow-sm transition-all hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700">
      <div className="flex items-start gap-4">
        <div className="shrink-0 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 p-3 text-indigo-600 dark:text-indigo-400 transition-colors group-hover:bg-indigo-200 dark:group-hover:bg-indigo-900/50">
          <Icon className="size-6" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-50 mb-2">
            {title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}
