"use client";

import * as React from "react";
import { RiCodeLine, RiTimeLine, RiCalendarLine, RiCpuLine } from "@remixicon/react";
import type { Assessment } from "@/types/representatives";

interface TechnicalMetaCardProps {
  assessment: Assessment;
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function TechnicalMetaCard({ assessment }: TechnicalMetaCardProps) {
  const metaItems = [
    {
      icon: RiCpuLine,
      label: "Model",
      value: assessment.model_name,
    },
    {
      icon: RiCodeLine,
      label: "Prompt Version",
      value: assessment.prompt_version,
    },
    {
      icon: RiTimeLine,
      label: "Latency",
      value: formatLatency(assessment.latency_ms),
    },
    {
      icon: RiCalendarLine,
      label: "Created",
      value: formatDateTime(assessment.created_at),
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800/50 bg-slate-950/30 p-4">
      <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
        Assessment Details
      </h3>
      <div className="flex flex-wrap gap-x-6 gap-y-2">
        {metaItems.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <item.icon className="h-3.5 w-3.5 text-slate-600" />
            <span className="text-xs text-slate-500">{item.label}:</span>
            <span className="text-xs text-slate-400 font-mono">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

