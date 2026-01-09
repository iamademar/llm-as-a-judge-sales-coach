"use client"

import React from "react"
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { VolumeDataPoint } from "@/types/overview"

interface VolumeQualityTrendCardProps {
  volumeData: VolumeDataPoint[]
  className?: string
}

export function VolumeQualityTrendCard({
  volumeData,
  className = "",
}: VolumeQualityTrendCardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 ${className}`}
    >
      <h2 className="mb-2 text-sm font-medium text-slate-200">
        Volume & quality trend
      </h2>
      <p className="mb-4 text-xs text-slate-400">
        Daily conversation volume and percentage above target (3.5)
      </p>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={volumeData}>
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
              yAxisId="left"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              stroke="#1e293b"
              label={{
                value: "Count",
                angle: -90,
                position: "insideLeft",
                style: { fill: "#94a3b8", fontSize: 11 },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              stroke="#1e293b"
              label={{
                value: "% Above Target",
                angle: 90,
                position: "insideRight",
                style: { fill: "#94a3b8", fontSize: 11 },
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#1e293b",
                color: "#e2e8f0",
                fontSize: 12,
                borderRadius: "0.5rem",
              }}
              formatter={(value: number, name: string) => {
                if (name === "Conversations") return [value, name]
                return [`${value}%`, name]
              }}
              labelFormatter={(label) => {
                const date = new Date(label)
                return date.toLocaleDateString()
              }}
            />
            <Legend wrapperStyle={{ fontSize: "11px" }} />
            <Bar
              yAxisId="left"
              dataKey="count"
              name="Conversations"
              fill="#6366f1"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="percentAboveTarget"
              name="% Above Target"
              stroke="#34d399"
              strokeWidth={2}
              dot={{ fill: "#34d399", r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

