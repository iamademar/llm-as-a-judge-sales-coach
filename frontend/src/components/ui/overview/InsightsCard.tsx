"use client"

import React from "react"
import { RiLightbulbLine } from "@remixicon/react"
import { InsightItem } from "@/types/overview"

interface InsightsCardProps {
  insights: InsightItem[]
  className?: string
}

export function InsightsCard({ insights, className = "" }: InsightsCardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3 ${className}`}
    >
      <div className="flex items-center gap-2">
        <RiLightbulbLine className="h-5 w-5 text-amber-400" />
        <h2 className="text-sm font-medium text-slate-200">
          This week&apos;s coaching insights
        </h2>
      </div>
      <p className="text-xs text-slate-400">
        AI-generated observations and recommendations
      </p>
      <ul className="space-y-2.5">
        {insights.map((insight, index) => (
          <li key={index} className="flex gap-2 text-xs text-slate-300">
            <span className="text-indigo-400 flex-shrink-0">•</span>
            <div className="space-y-0.5">
              <p className="font-medium text-slate-200">{insight.title}</p>
              <p className="text-slate-400">{insight.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
