"use client";

import * as React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  Tooltip as RechartsTooltip,
} from "recharts";
import { Tooltip } from "@/components/Tooltip";
import type { AssessmentScores } from "@/types/representatives";

interface SpinScoresChartProps {
  scores: AssessmentScores;
}

const SPIN_DESCRIPTIONS: Record<string, string> = {
  situation: "Quality of situation questions - understanding the customer's current state",
  problem: "Quality of problem questions - uncovering customer pain points",
  implication: "Quality of implication questions - exploring consequences of problems",
  need_payoff: "Quality of need-payoff questions - demonstrating solution value",
};

function getBarColor(score: number): string {
  if (score >= 4) return "#34d399"; // emerald-400
  if (score >= 3) return "#fbbf24"; // amber-400
  return "#f87171"; // rose-400
}

function getSemanticLabel(score: number): string {
  if (score >= 4) return "Good";
  if (score >= 3) return "Average";
  if (score >= 2) return "Below average";
  return "Poor";
}

function getLabelColor(score: number): string {
  if (score >= 4) return "text-emerald-400";
  if (score >= 3) return "text-amber-400";
  return "text-rose-400";
}

export function SpinScoresChart({ scores }: SpinScoresChartProps) {
  const chartData = [
    { name: "S", fullName: "Situation", value: scores.situation, key: "situation" },
    { name: "P", fullName: "Problem", value: scores.problem, key: "problem" },
    { name: "I", fullName: "Implication", value: scores.implication, key: "implication" },
    { name: "N", fullName: "Need-Payoff", value: scores.need_payoff, key: "need_payoff" },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-medium text-slate-200 mb-4">SPIN Scores</h3>

      {/* Horizontal Bar Chart */}
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 20, left: 0, bottom: 0 }}
          >
            <XAxis
              type="number"
              domain={[0, 5]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "#94a3b8", fontSize: 12, fontWeight: 500 }}
              tickLine={false}
              axisLine={false}
              width={24}
            />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#1e293b",
                color: "#e2e8f0",
                fontSize: 12,
                borderRadius: "0.5rem",
              }}
              formatter={(value: number, _name: string, props: any) => [
                `${value}/5 - ${getSemanticLabel(value)}`,
                props.payload.fullName,
              ]}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Mini dimension cards */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        {chartData.map((item) => (
          <Tooltip
            key={item.key}
            content={SPIN_DESCRIPTIONS[item.key]}
            side="bottom"
          >
            <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 cursor-help">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">{item.fullName}</span>
                <span className={`text-lg font-semibold ${getLabelColor(item.value)}`}>
                  {item.value}
                </span>
              </div>
              <span className={`text-xs ${getLabelColor(item.value)}`}>
                {getSemanticLabel(item.value)}
              </span>
            </div>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}

