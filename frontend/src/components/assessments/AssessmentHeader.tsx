"use client";

import * as React from "react";
import { RiArrowLeftLine, RiRefreshLine, RiFileDownloadLine } from "@remixicon/react";
import { Button } from "@/components/Button";
import { Badge } from "@/components/Badge";
import { Tooltip } from "@/components/Tooltip";
import type { Transcript, Assessment, Representative } from "@/types/representatives";

interface AssessmentHeaderProps {
  transcript: Transcript;
  assessment: Assessment;
  representative: Representative | null;
  onBack: () => void;
}

function calculateCompositeScore(scores: Assessment["scores"]): number {
  const { situation, problem, implication, need_payoff, flow, tone, engagement } = scores;
  return (situation + problem + implication + need_payoff + flow + tone + engagement) / 7;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function AssessmentHeader({
  transcript,
  assessment,
  representative,
  onBack,
}: AssessmentHeaderProps) {
  const compositeScore = calculateCompositeScore(assessment.scores);
  const repName = representative?.full_name || "Unknown Rep";
  const buyerId = transcript.buyer_id || "Unknown Buyer";

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      {/* Left side: Back button + context info */}
      <div className="flex items-start gap-4">
        <Button
          variant="ghost"
          className="p-2 shrink-0"
          onClick={onBack}
        >
          <RiArrowLeftLine className="h-5 w-5" />
        </Button>
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl font-semibold text-slate-100">
              {repName}
            </h1>
            <span className="text-slate-500">•</span>
            <span className="text-slate-300">{buyerId}</span>
          </div>
          <div className="flex items-center gap-2 mt-1 text-sm text-slate-400 flex-wrap">
            <span>{formatDate(transcript.created_at)}</span>
            <span>·</span>
            <span>{formatTime(transcript.created_at)}</span>
            <span>·</span>
            <span className="font-medium text-indigo-400">
              {compositeScore.toFixed(2)} SPIN Score
            </span>
          </div>
        </div>
      </div>

      {/* Right side: Status badges + actions */}
      <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
        {/* Status badges */}
        <Badge variant="success">Completed</Badge>
        {representative?.is_active && (
          <Badge variant="default">Active</Badge>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Tooltip content="Re-run analysis" side="bottom">
            <Button
              variant="secondary"
              className="p-2 border-slate-700 bg-slate-900 hover:bg-slate-800"
              disabled
            >
              <RiRefreshLine className="h-4 w-4" />
            </Button>
          </Tooltip>
          <Tooltip content="Export PDF" side="bottom">
            <Button
              variant="secondary"
              className="p-2 border-slate-700 bg-slate-900 hover:bg-slate-800"
              disabled
            >
              <RiFileDownloadLine className="h-4 w-4" />
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

