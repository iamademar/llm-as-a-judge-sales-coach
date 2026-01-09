"use client";

import * as React from "react";
import type { AssessmentScores } from "@/types/representatives";

interface QualityScoresRowProps {
  scores: AssessmentScores;
}

function getSemanticLabel(score: number): string {
  if (score >= 4) return "Good";
  if (score >= 3) return "Average";
  if (score >= 2) return "Below average";
  return "Poor";
}

function getScoreColor(score: number): string {
  if (score >= 4) return "text-emerald-400";
  if (score >= 3) return "text-amber-400";
  return "text-rose-400";
}

function getScoreBgColor(score: number): string {
  if (score >= 4) return "bg-emerald-500/10 border-emerald-500/20";
  if (score >= 3) return "bg-amber-500/10 border-amber-500/20";
  return "bg-rose-500/10 border-rose-500/20";
}

export function QualityScoresRow({ scores }: QualityScoresRowProps) {
  const qualityMetrics = [
    { label: "Flow", value: scores.flow, description: "Overall conversation flow" },
    { label: "Tone", value: scores.tone, description: "Tone and professionalism" },
    { label: "Engagement", value: scores.engagement, description: "Customer engagement level" },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-medium text-slate-200 mb-4">Conversation Quality</h3>
      <div className="grid grid-cols-3 gap-3">
        {qualityMetrics.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-lg border p-3 text-center ${getScoreBgColor(metric.value)}`}
          >
            <span className={`text-2xl font-bold ${getScoreColor(metric.value)}`}>
              {metric.value}
            </span>
            <p className="mt-1 text-sm font-medium text-slate-300">{metric.label}</p>
            <p className={`text-xs ${getScoreColor(metric.value)}`}>
              {getSemanticLabel(metric.value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

