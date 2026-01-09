"use client";

import * as React from "react";
import { RiCheckLine, RiCloseLine } from "@remixicon/react";
import { Checkbox } from "@/components/Checkbox";
import type { AssessmentCoaching } from "@/types/representatives";

interface CoachingPanelProps {
  coaching: AssessmentCoaching;
}

type TabKey = "wins" | "gaps" | "actions";

export function CoachingPanel({ coaching }: CoachingPanelProps) {
  const [activeTab, setActiveTab] = React.useState<TabKey>("wins");

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: "wins", label: "Wins", count: coaching.wins.length },
    { key: "gaps", label: "Gaps", count: coaching.gaps.length },
    { key: "actions", label: "Next Actions", count: coaching.next_actions.length },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 h-full">
      {/* Summary */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-slate-200 mb-2">Coaching Summary</h3>
        <p className="text-sm text-slate-400 leading-relaxed">{coaching.summary}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeTab === tab.key
                  ? "text-indigo-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-1.5 text-xs text-slate-500">({tab.count})</span>
              )}
              {activeTab === tab.key && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-4 min-h-[200px]">
        {activeTab === "wins" && (
          <ul className="space-y-3">
            {coaching.wins.length === 0 ? (
              <li className="text-sm text-slate-500 italic">No wins recorded</li>
            ) : (
              coaching.wins.map((win, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/20">
                    <RiCheckLine className="h-3 w-3 text-emerald-400" />
                  </span>
                  <span className="text-sm text-slate-300">{win}</span>
                </li>
              ))
            )}
          </ul>
        )}

        {activeTab === "gaps" && (
          <ul className="space-y-3">
            {coaching.gaps.length === 0 ? (
              <li className="text-sm text-slate-500 italic">No gaps identified</li>
            ) : (
              coaching.gaps.map((gap, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-rose-500/20">
                    <RiCloseLine className="h-3 w-3 text-rose-400" />
                  </span>
                  <span className="text-sm text-slate-300">{gap}</span>
                </li>
              ))
            )}
          </ul>
        )}

        {activeTab === "actions" && (
          <ul className="space-y-3">
            {coaching.next_actions.length === 0 ? (
              <li className="text-sm text-slate-500 italic">No actions suggested</li>
            ) : (
              coaching.next_actions.map((action, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Checkbox
                    className="mt-0.5 shrink-0"
                    aria-label={`Mark "${action}" as complete`}
                  />
                  <span className="text-sm text-slate-300">{action}</span>
                </li>
              ))
            )}
          </ul>
        )}
      </div>
    </div>
  );
}

