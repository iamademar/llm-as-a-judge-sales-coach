"use client";

import * as React from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { twMerge } from "tailwind-merge";
import {
  RiChatVoiceLine,
  RiBarChartBoxLine,
  RiTimeLine,
  RiUserLine,
} from "@remixicon/react";
import { LineChart } from "@/components/LineChart";
import { TranscriptsTable } from "./TranscriptsTable";
import type {
  Representative,
  Transcript,
  Assessment,
} from "@/types/representatives";

interface Props {
  representative: Representative;
  transcripts: Transcript[];
  assessments: Assessment[];
  onRefresh: () => void;
}

export function RepDetailTabs({
  representative,
  transcripts,
  assessments,
  onRefresh,
}: Props) {
  // Calculate composite SPIN score from assessment scores
  const calculateCompositeScore = (scores: Assessment["scores"]): number => {
    const {
      situation,
      problem,
      implication,
      need_payoff,
      flow,
      tone,
      engagement,
    } = scores;
    return (
      (situation + problem + implication + need_payoff + flow + tone + engagement) /
      7
    );
  };

  // Get assessments for transcripts belonging to this representative
  const repAssessments = React.useMemo(() => {
    const transcriptIds = new Set(transcripts.map((t) => t.id));
    return assessments.filter((a) => transcriptIds.has(a.transcript_id));
  }, [transcripts, assessments]);

  // Calculate metrics
  const metrics = React.useMemo(() => {
    const totalConversations = transcripts.length;
    
    let avgSpinScore: number | null = null;
    if (repAssessments.length > 0) {
      const total = repAssessments.reduce(
        (sum, a) => sum + calculateCompositeScore(a.scores),
        0
      );
      avgSpinScore = total / repAssessments.length;
    }

    const lastConversationDate = transcripts.length > 0
      ? new Date(
          Math.max(...transcripts.map((t) => new Date(t.created_at).getTime()))
        ).toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
        })
      : null;

    const completedCount = repAssessments.length;
    const pendingCount = transcripts.length - repAssessments.length;

    return {
      totalConversations,
      avgSpinScore,
      lastConversationDate,
      completedCount,
      pendingCount,
    };
  }, [transcripts, repAssessments]);

  // Prepare chart data: SPIN score over time
  const chartData = React.useMemo(() => {
    // Create a map of transcript_id to assessment
    const assessmentMap = new Map(repAssessments.map((a) => [a.transcript_id, a]));

    // Get transcripts with assessments, sorted by date
    const transcriptsWithAssessments = transcripts
      .filter((t) => assessmentMap.has(t.id))
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    return transcriptsWithAssessments.map((t) => {
      const assessment = assessmentMap.get(t.id)!;
      const score = calculateCompositeScore(assessment.scores);
      const date = new Date(t.created_at);
      return {
        date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        title: `Conversation with ${t.buyer_id || "Unknown"}`,
        formattedDate: date.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
        "SPIN Score": parseFloat(score.toFixed(2)),
      };
    });
  }, [transcripts, repAssessments]);

  // Recent conversations (last 5)
  const recentConversations = React.useMemo(() => {
    const assessmentMap = new Map(repAssessments.map((a) => [a.transcript_id, a]));
    
    return [...transcripts]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5)
      .map((t) => {
        const assessment = assessmentMap.get(t.id);
        return {
          id: t.id,
          buyerId: t.buyer_id || "Unknown",
          date: new Date(t.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
          }),
          score: assessment ? calculateCompositeScore(assessment.scores) : null,
          status: assessment ? "completed" : "pending",
        };
      });
  }, [transcripts, repAssessments]);

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-slate-500";
    if (score >= 3.5) return "text-emerald-400";
    if (score >= 3) return "text-amber-300";
    return "text-rose-400";
  };

  return (
    <Tabs.Root defaultValue="overview" className="space-y-6">
      <Tabs.List className="flex border-b border-slate-800">
        <Tabs.Trigger
          value="overview"
          className={twMerge(
            "relative px-4 py-2.5 text-sm font-medium transition-colors",
            "text-slate-400 hover:text-slate-200",
            "data-[state=active]:text-indigo-400",
            "after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5",
            "after:scale-x-0 data-[state=active]:after:scale-x-100",
            "after:bg-indigo-500 after:transition-transform"
          )}
        >
          <span className="flex items-center gap-2">
            <RiBarChartBoxLine className="h-4 w-4" />
            Overview
          </span>
        </Tabs.Trigger>
        <Tabs.Trigger
          value="conversations"
          className={twMerge(
            "relative px-4 py-2.5 text-sm font-medium transition-colors",
            "text-slate-400 hover:text-slate-200",
            "data-[state=active]:text-indigo-400",
            "after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5",
            "after:scale-x-0 data-[state=active]:after:scale-x-100",
            "after:bg-indigo-500 after:transition-transform"
          )}
        >
          <span className="flex items-center gap-2">
            <RiChatVoiceLine className="h-4 w-4" />
            Conversations
            <span className="ml-1 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
              {transcripts.length}
            </span>
          </span>
        </Tabs.Trigger>
      </Tabs.List>

      {/* Overview Tab */}
      <Tabs.Content value="overview" className="space-y-6">
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2">
              <RiChatVoiceLine className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-medium text-slate-400">Total Conversations</p>
            </div>
            <p className="mt-2 text-2xl font-semibold text-slate-100">
              {metrics.totalConversations}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2">
              <RiBarChartBoxLine className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-medium text-slate-400">Avg SPIN Score</p>
            </div>
            <p className={twMerge("mt-2 text-2xl font-semibold", getScoreColor(metrics.avgSpinScore))}>
              {metrics.avgSpinScore !== null ? metrics.avgSpinScore.toFixed(2) : "—"}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2">
              <RiTimeLine className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-medium text-slate-400">Last Conversation</p>
            </div>
            <p className="mt-2 text-lg font-semibold text-slate-100">
              {metrics.lastConversationDate || "—"}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2">
              <RiUserLine className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-medium text-slate-400">Department</p>
            </div>
            <p className="mt-2 text-lg font-semibold text-slate-100">
              {representative.department || "—"}
            </p>
          </div>
        </div>

        {/* SPIN Trend Chart */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <h3 className="mb-4 text-sm font-medium text-slate-300">SPIN Score Trend</h3>
          {chartData.length > 0 ? (
            <LineChart
              data={chartData}
              index="date"
              categories={["SPIN Score"]}
              colors={["indigo"]}
              valueFormatter={(value) => value.toFixed(2)}
              showLegend={false}
              className="h-64"
              yAxisWidth={40}
              minValue={1}
              maxValue={5}
            />
          ) : (
            <div className="flex h-64 items-center justify-center">
              <p className="text-sm text-slate-500">No assessment data yet</p>
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-300">Recent Conversations</h3>
            <Tabs.List>
              <Tabs.Trigger
                value="conversations"
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                View all →
              </Tabs.Trigger>
            </Tabs.List>
          </div>
          {recentConversations.length > 0 ? (
            <div className="space-y-2">
              {recentConversations.map((conv) => (
                <div
                  key={conv.id}
                  className="flex items-center justify-between rounded-md bg-slate-900/50 px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-slate-200">{conv.buyerId}</span>
                    <span className="text-xs text-slate-500">{conv.date}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={twMerge("text-sm font-medium", getScoreColor(conv.score))}>
                      {conv.score !== null ? conv.score.toFixed(2) : "—"}
                    </span>
                    <span
                      className={twMerge(
                        "rounded-full px-2 py-0.5 text-xs",
                        conv.status === "completed"
                          ? "bg-emerald-900/40 text-emerald-300"
                          : "bg-amber-900/40 text-amber-300"
                      )}
                    >
                      {conv.status === "completed" ? "Completed" : "Pending"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-4 text-center text-sm text-slate-500">No conversations yet</p>
          )}
        </div>
      </Tabs.Content>

      {/* Conversations Tab */}
      <Tabs.Content value="conversations">
        <TranscriptsTable
          transcripts={transcripts}
          assessments={assessments}
          onRefresh={onRefresh}
        />
      </Tabs.Content>
    </Tabs.Root>
  );
}

