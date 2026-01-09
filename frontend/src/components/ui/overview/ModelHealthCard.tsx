"use client"

import React from "react"
import { ModelHealthData } from "@/types/overview"

interface ModelHealthCardProps {
  healthData: ModelHealthData
  className?: string
}

export function ModelHealthCard({
  healthData,
  className = "",
}: ModelHealthCardProps) {
  const statusConfig = {
    healthy: {
      label: "Healthy",
      icon: "✅",
      color: "text-emerald-400",
      description: "Model performance within accepted range",
    },
    warning: {
      label: "Needs Attention",
      icon: "⚠️",
      color: "text-amber-400",
      description: "Model performance below target threshold",
    },
    critical: {
      label: "Critical",
      icon: "❌",
      color: "text-rose-400",
      description: "Model performance critically low—action required",
    },
  }

  const status = statusConfig[healthData.status]

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3 ${className}`}
    >
      <h2 className="text-sm font-medium text-slate-200">Model calibration</h2>
      <p className="text-xs text-slate-400">
        Last eval on gold set •{" "}
        {new Date(healthData.lastEvalDate).toLocaleDateString()}
      </p>

      {/* Model Info */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Model</span>
          <span className="text-xs font-medium text-slate-200">
            {healthData.modelName}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Prompt version</span>
          <span className="text-xs font-medium text-slate-200">
            {healthData.promptVersion}
          </span>
        </div>
      </div>

      {/* Metrics */}
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs border-t border-slate-800 pt-3">
        <div>
          <dt className="text-slate-400">Macro Pearson r</dt>
          <dd className="mt-1 text-base font-medium text-slate-100">
            {healthData.macroPearsonR.toFixed(2)}
          </dd>
        </div>
        <div>
          <dt className="text-slate-400">Macro QWK</dt>
          <dd className="mt-1 text-base font-medium text-slate-100">
            {healthData.macroQWK.toFixed(2)}
          </dd>
        </div>

        {/* Only show latency if data exists */}
        {healthData.avgLatencyMs != null && (
          <div className="col-span-2">
            <dt className="text-slate-400">Avg latency</dt>
            <dd className="mt-1 text-base font-medium text-slate-100">
              {healthData.avgLatencyMs.toLocaleString()} ms
            </dd>
          </div>
        )}
      </dl>

      {/* Status */}
      <div className="flex items-center gap-2 border-t border-slate-800 pt-3">
        <span className="text-lg">{status.icon}</span>
        <div>
          <p className={`text-sm font-medium ${status.color}`}>
            {status.label}
          </p>
          <p className="text-xs text-slate-400">
            {status.description}
          </p>
        </div>
      </div>
    </div>
  )
}

