/**
 * Mock data for SPIN Overview Dashboard
 * This file contains sample data for development and testing
 */

import type {
  OverviewSummary,
  SpinRadarData,
  QueueItem,
  TrendDataPoint,
  VolumeDataPoint,
  ModelHealthData,
  RepStats,
  FilterOptions,
} from "@/types/overview"

// KPI Summary
export const mockOverviewSummary: OverviewSummary = {
  totalConversations: 243,
  avgCompositeScore: 3.7,
  percentageAboveTarget: 62,
  weakestDimension: "Implication",
  deltaConversations: "+18%",
  deltaScore: "+0.2",
  deltaPercentage: "-3%",
}

// SPIN Radar Data
export const mockSpinRadarData: SpinRadarData[] = [
  { dimension: "Situation", value: 4.1 },
  { dimension: "Problem", value: 3.8 },
  { dimension: "Implication", value: 2.9 },
  { dimension: "Need-payoff", value: 3.4 },
  { dimension: "Flow", value: 3.6 },
  { dimension: "Tone", value: 4.2 },
  { dimension: "Engagement", value: 3.9 },
]

// Coaching Queue Items
export const mockQueueItems: QueueItem[] = [
  {
    id: "1",
    rep: "Alex Thang",
    buyer: "Acme Corp",
    composite: 2.8,
    weakestDim: "Implication",
    createdAt: "2025-11-27T09:00:00Z",
  },
  {
    id: "2",
    rep: "Sarah Chen",
    buyer: "TechStart Inc",
    composite: 2.5,
    weakestDim: "Need-payoff",
    createdAt: "2025-11-27T08:30:00Z",
  },
  {
    id: "3",
    rep: "Michael Ross",
    buyer: "Global Solutions",
    composite: 2.9,
    weakestDim: "Problem",
    createdAt: "2025-11-26T16:45:00Z",
  },
  {
    id: "4",
    rep: "Jessica Liu",
    buyer: "Enterprise Co",
    composite: 3.0,
    weakestDim: "Implication",
    createdAt: "2025-11-26T14:20:00Z",
  },
  {
    id: "5",
    rep: "David Park",
    buyer: "Innovate Labs",
    composite: 2.7,
    weakestDim: "Situation",
    createdAt: "2025-11-26T11:00:00Z",
  },
  {
    id: "6",
    rep: "Emma Wilson",
    buyer: "Future Systems",
    composite: 2.6,
    weakestDim: "Flow",
    createdAt: "2025-11-25T15:30:00Z",
  },
  {
    id: "7",
    rep: "James Kim",
    buyer: "DataWorks",
    composite: 3.2,
    weakestDim: "Engagement",
    createdAt: "2025-11-25T10:15:00Z",
  },
  {
    id: "8",
    rep: "Olivia Martinez",
    buyer: "CloudFirst",
    composite: 2.4,
    weakestDim: "Need-payoff",
    createdAt: "2025-11-24T17:00:00Z",
  },
]

// Trend Data (Last 30 days)
export const mockTrendData: TrendDataPoint[] = [
  { date: "2025-10-28", situation: 3.8, problem: 3.5, implication: 2.7, need_payoff: 3.2, flow: 3.4, tone: 4.0, engagement: 3.7 },
  { date: "2025-10-29", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-10-30", situation: 3.7, problem: 3.4, implication: 2.6, need_payoff: 3.1, flow: 3.3, tone: 3.9, engagement: 3.6 },
  { date: "2025-10-31", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-01", situation: 3.8, problem: 3.5, implication: 2.7, need_payoff: 3.2, flow: 3.4, tone: 4.0, engagement: 3.7 },
  { date: "2025-11-02", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-11-03", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-04", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-05", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-11-06", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-07", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-08", situation: 4.2, problem: 3.9, implication: 3.1, need_payoff: 3.6, flow: 3.8, tone: 4.4, engagement: 4.1 },
  { date: "2025-11-09", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-10", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-11-11", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-12", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-13", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-14", situation: 4.2, problem: 3.9, implication: 3.1, need_payoff: 3.6, flow: 3.8, tone: 4.4, engagement: 4.1 },
  { date: "2025-11-15", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-16", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-11-17", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-18", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-19", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-20", situation: 4.2, problem: 3.9, implication: 3.1, need_payoff: 3.6, flow: 3.8, tone: 4.4, engagement: 4.1 },
  { date: "2025-11-21", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-22", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-23", situation: 3.9, problem: 3.6, implication: 2.8, need_payoff: 3.3, flow: 3.5, tone: 4.1, engagement: 3.8 },
  { date: "2025-11-24", situation: 4.1, problem: 3.8, implication: 3.0, need_payoff: 3.5, flow: 3.7, tone: 4.3, engagement: 4.0 },
  { date: "2025-11-25", situation: 4.0, problem: 3.7, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
  { date: "2025-11-26", situation: 4.1, problem: 3.8, implication: 2.9, need_payoff: 3.4, flow: 3.6, tone: 4.2, engagement: 3.9 },
]

// Volume and Quality Data
export const mockVolumeData: VolumeDataPoint[] = [
  { date: "2025-10-28", count: 7, percentAboveTarget: 57 },
  { date: "2025-10-29", count: 9, percentAboveTarget: 61 },
  { date: "2025-10-30", count: 6, percentAboveTarget: 50 },
  { date: "2025-10-31", count: 11, percentAboveTarget: 64 },
  { date: "2025-11-01", count: 8, percentAboveTarget: 58 },
  { date: "2025-11-02", count: 10, percentAboveTarget: 62 },
  { date: "2025-11-03", count: 12, percentAboveTarget: 68 },
  { date: "2025-11-04", count: 9, percentAboveTarget: 60 },
  { date: "2025-11-05", count: 8, percentAboveTarget: 59 },
  { date: "2025-11-06", count: 10, percentAboveTarget: 63 },
  { date: "2025-11-07", count: 11, percentAboveTarget: 65 },
  { date: "2025-11-08", count: 13, percentAboveTarget: 70 },
  { date: "2025-11-09", count: 9, percentAboveTarget: 61 },
  { date: "2025-11-10", count: 7, percentAboveTarget: 56 },
  { date: "2025-11-11", count: 10, percentAboveTarget: 64 },
  { date: "2025-11-12", count: 9, percentAboveTarget: 62 },
  { date: "2025-11-13", count: 11, percentAboveTarget: 66 },
  { date: "2025-11-14", count: 12, percentAboveTarget: 69 },
  { date: "2025-11-15", count: 8, percentAboveTarget: 60 },
  { date: "2025-11-16", count: 7, percentAboveTarget: 58 },
  { date: "2025-11-17", count: 10, percentAboveTarget: 65 },
  { date: "2025-11-18", count: 9, percentAboveTarget: 63 },
  { date: "2025-11-19", count: 11, percentAboveTarget: 67 },
  { date: "2025-11-20", count: 13, percentAboveTarget: 71 },
  { date: "2025-11-21", count: 10, percentAboveTarget: 64 },
  { date: "2025-11-22", count: 9, percentAboveTarget: 62 },
  { date: "2025-11-23", count: 8, percentAboveTarget: 59 },
  { date: "2025-11-24", count: 10, percentAboveTarget: 65 },
  { date: "2025-11-25", count: 9, percentAboveTarget: 63 },
  { date: "2025-11-26", count: 11, percentAboveTarget: 66 },
]

// Model Health Data
export const mockModelHealthData: ModelHealthData = {
  modelName: "gpt-4o-mini",
  promptVersion: "spin_v3",
  lastEvalDate: "2025-11-20",
  macroPearsonR: 0.78,
  macroQWK: 0.73,
  avgLatencyMs: 1250,
  status: "healthy",
}

// Rep Leaderboard
export const mockRepStats: RepStats[] = [
  { rank: 1, rep: "Emma Wilson", conversationCount: 28, avgComposite: 4.2, strongest: "Tone", strongestScore: 4.8, weakest: "Implication", weakestScore: 3.6, trend: 0.3 },
  { rank: 2, rep: "James Kim", conversationCount: 32, avgComposite: 4.0, strongest: "Situation", strongestScore: 4.6, weakest: "Need-payoff", weakestScore: 3.5, trend: 0.2 },
  { rank: 3, rep: "Sarah Chen", conversationCount: 25, avgComposite: 3.9, strongest: "Problem", strongestScore: 4.5, weakest: "Flow", weakestScore: 3.4, trend: 0.1 },
  { rank: 4, rep: "Alex Thang", conversationCount: 30, avgComposite: 3.7, strongest: "Engagement", strongestScore: 4.3, weakest: "Implication", weakestScore: 3.0, trend: -0.1 },
  { rank: 5, rep: "Michael Ross", conversationCount: 27, avgComposite: 3.6, strongest: "Tone", strongestScore: 4.2, weakest: "Problem", weakestScore: 3.1, trend: 0.0 },
  { rank: 6, rep: "Jessica Liu", conversationCount: 23, avgComposite: 3.5, strongest: "Situation", strongestScore: 4.1, weakest: "Implication", weakestScore: 2.9, trend: 0.2 },
  { rank: 7, rep: "David Park", conversationCount: 26, avgComposite: 3.4, strongest: "Flow", strongestScore: 4.0, weakest: "Situation", weakestScore: 2.8, trend: -0.2 },
  { rank: 8, rep: "Olivia Martinez", conversationCount: 22, avgComposite: 3.2, strongest: "Engagement", strongestScore: 3.9, weakest: "Need-payoff", weakestScore: 2.6, trend: -0.3 },
]

// Insights
export const mockInsights: string[] = [
  "Reps improved Need-payoff by +0.3 on average vs last week",
  "Top 3 recurring gap themes: weak problem deepening, jumping to demo, vague next steps",
  "Team members to spotlight: Emma Wilson (strong Tone: 4.8), James Kim (high Situation: 4.6)",
  "8 conversations need immediate coaching attention (composite < 3.0)",
  "Implication questions remain the weakest dimension across the team (avg: 2.9)",
]

// Filter Options
export const mockFilterOptions: FilterOptions = {
  reps: ["All Reps", "Alex Thang", "Sarah Chen", "Michael Ross", "Jessica Liu", "David Park", "Emma Wilson", "James Kim", "Olivia Martinez"],
  channels: ["All", "Calls", "Emails"],
  models: ["All Models", "gpt-4o-mini", "gpt-4o", "claude-3-sonnet"],
  promptVersions: ["All Versions", "spin_v3", "spin_v2", "spin_v1"],
}

