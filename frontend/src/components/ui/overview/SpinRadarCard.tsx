"use client"

import React from "react"
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts"
import { SpinRadarData } from "@/types/overview"

interface SpinRadarCardProps {
  data: SpinRadarData[]
  className?: string
}

export function SpinRadarCard({ data, className = "" }: SpinRadarCardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 ${className}`}
    >
      <h2 className="mb-2 text-sm font-medium text-slate-200">
        SPIN profile (team average)
      </h2>
      <p className="mb-4 text-xs text-slate-400">
        Average scores across all dimensions (1-5 scale)
      </p>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="75%">
            <PolarGrid stroke="#1e293b" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[1, 5]}
              tick={{ fill: "#64748b", fontSize: 10 }}
              stroke="#1e293b"
            />
            <Radar
              name="Average"
              dataKey="value"
              fill="rgba(129, 140, 248, 0.5)"
              stroke="#818cf8"
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#1e293b",
                color: "#e2e8f0",
                fontSize: 12,
                borderRadius: "0.5rem",
              }}
              formatter={(value: number) => [value.toFixed(2), "Score"]}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

