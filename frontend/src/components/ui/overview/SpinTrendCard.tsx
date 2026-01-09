"use client"

import React from "react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { TrendDataPoint } from "@/types/overview"

interface SpinTrendCardProps {
  trendData: TrendDataPoint[]
  className?: string
}

export function SpinTrendCard({
  trendData,
  className = "",
}: SpinTrendCardProps) {
  const [visibleLines, setVisibleLines] = React.useState({
    situation: true,
    problem: true,
    implication: true,
    need_payoff: true,
    flow: true,
    tone: true,
    engagement: true,
  })

  const dimensions = [
    { key: "situation", label: "Situation", color: "#818cf8" },
    { key: "problem", label: "Problem", color: "#a78bfa" },
    { key: "implication", label: "Implication", color: "#c084fc" },
    { key: "need_payoff", label: "Need-payoff", color: "#e879f9" },
    { key: "flow", label: "Flow", color: "#f472b6" },
    { key: "tone", label: "Tone", color: "#fb923c" },
    { key: "engagement", label: "Engagement", color: "#34d399" },
  ]

  const toggleLine = (key: string) => {
    setVisibleLines((prev) => ({ ...prev, [key]: !prev[key as keyof typeof prev] }))
  }

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 ${className}`}
    >
      <h2 className="mb-2 text-sm font-medium text-slate-200">
        SPIN scores over time
      </h2>
      <p className="mb-4 text-xs text-slate-400">
        Daily average scores for each SPIN dimension
      </p>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              stroke="#1e293b"
              tickFormatter={(value) => {
                const date = new Date(value)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis
              domain={[1, 5]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              stroke="#1e293b"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#1e293b",
                color: "#e2e8f0",
                fontSize: 12,
                borderRadius: "0.5rem",
              }}
              formatter={(value: number) => value.toFixed(2)}
              labelFormatter={(label) => {
                const date = new Date(label)
                return date.toLocaleDateString()
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px" }}
              onClick={(e) => toggleLine(e.dataKey as string)}
              iconType="line"
            />
            {dimensions.map(
              (dim) =>
                visibleLines[dim.key as keyof typeof visibleLines] && (
                  <Line
                    key={dim.key}
                    type="monotone"
                    dataKey={dim.key}
                    name={dim.label}
                    stroke={dim.color}
                    strokeWidth={2}
                    dot={false}
                  />
                )
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

