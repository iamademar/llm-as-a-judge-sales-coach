"use client"

import React from "react"
import { OverviewSummary } from "@/types/overview"

interface KpiGridProps {
  data: OverviewSummary
}

export function KpiGrid({ data }: KpiGridProps) {
  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Conversations analyzed"
        value={data.totalConversations.toLocaleString()}
        delta={data.deltaConversations}
        deltaPositive={data.deltaConversations?.startsWith("+")}
        sublabel="vs previous period"
      />
      <KpiCard
        label="Avg SPIN score"
        value={data.avgCompositeScore.toFixed(1)}
        delta={data.deltaScore}
        deltaPositive={data.deltaScore?.startsWith("+")}
        sublabel="Target: 3.5+"
      />
      <KpiCard
        label="Above target"
        value={`${data.percentageAboveTarget}%`}
        delta={data.deltaPercentage}
        deltaPositive={data.deltaPercentage?.startsWith("+")}
        sublabel="Calls ≥ 3.5 composite"
      />
      <KpiCard
        label="Weakest dimension"
        value={data.weakestDimension}
        sublabel="Focus area this period"
      />
    </section>
  )
}

interface KpiCardProps {
  label: string
  value: string
  delta?: string
  deltaPositive?: boolean
  sublabel?: string
}

function KpiCard({
  label,
  value,
  delta,
  deltaPositive,
  sublabel,
}: KpiCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>{label}</span>
        {delta && (
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${
              deltaPositive
                ? "bg-emerald-900/50 text-emerald-400"
                : "bg-rose-900/40 text-rose-400"
            }`}
          >
            {deltaPositive ? "↑" : "↓"} {delta.replace(/[+-]/, "")}
          </span>
        )}
      </div>
      <div className="text-2xl font-semibold text-slate-50">{value}</div>
      {sublabel && <div className="text-xs text-slate-500">{sublabel}</div>}
    </div>
  )
}

