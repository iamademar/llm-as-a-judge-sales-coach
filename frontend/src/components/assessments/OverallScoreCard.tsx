"use client";

import * as React from "react";
import type { AssessmentScores } from "@/types/representatives";

interface OverallScoreCardProps {
  scores: AssessmentScores;
}

function calculateCompositeScore(scores: AssessmentScores): number {
  const { situation, problem, implication, need_payoff, flow, tone, engagement } = scores;
  return (situation + problem + implication + need_payoff + flow + tone + engagement) / 7;
}

function getScoreColor(score: number): string {
  if (score >= 4) return "text-emerald-400";
  if (score >= 3) return "text-amber-400";
  return "text-rose-400";
}

function getScoreBgColor(score: number): string {
  if (score >= 4) return "bg-emerald-500/20";
  if (score >= 3) return "bg-amber-500/20";
  return "bg-rose-500/20";
}

export function OverallScoreCard({ scores }: OverallScoreCardProps) {
  const compositeScore = calculateCompositeScore(scores);
  const scoreColor = getScoreColor(compositeScore);
  const scoreBg = getScoreBgColor(compositeScore);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400 uppercase tracking-wide">
            Overall Assessment
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Based on 7 dimensions (SPIN + flow, tone, engagement)
          </p>
        </div>
        <div
          className={`flex h-16 w-16 items-center justify-center rounded-xl ${scoreBg}`}
        >
          <span className={`text-3xl font-bold ${scoreColor}`}>
            {compositeScore.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Score scale legend */}
      <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-rose-400" />
          <span>1-2 Poor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-400" />
          <span>3 Average</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span>4-5 Good</span>
        </div>
      </div>
    </div>
  );
}

