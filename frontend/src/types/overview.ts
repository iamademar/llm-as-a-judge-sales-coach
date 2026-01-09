/**
 * TypeScript type definitions for SPIN Overview Dashboard
 */

export interface OverviewSummary {
  totalConversations: number
  avgCompositeScore: number
  percentageAboveTarget: number
  weakestDimension: string
  dimensionAverages?: SpinRadarData[]
  deltaConversations?: string
  deltaScore?: string
  deltaPercentage?: string
}

export interface SpinRadarData {
  dimension: string
  value: number
}

export interface QueueItem {
  id: string
  rep: string
  buyer: string
  composite: number
  weakestDim: string
  createdAt: string
}

export interface TrendDataPoint {
  date: string
  situation: number
  problem: number
  implication: number
  need_payoff: number
  flow: number
  tone: number
  engagement: number
  conversation_count: number
  percent_above_target: number
}

export interface VolumeDataPoint {
  date: string
  count: number
  percentAboveTarget: number
}

export interface InsightItem {
  title: string
  detail: string
}

export interface ModelHealthData {
  modelName: string
  promptVersion: string
  lastEvalDate: string
  macroPearsonR: number
  macroQWK: number
  avgLatencyMs?: number  // Optional - may not exist if no latency data
  status: "healthy" | "warning" | "critical"
}

export interface RepStats {
  rank: number
  rep: string
  conversationCount: number
  avgComposite: number
  strongest: string
  strongestScore: number
  weakest: string
  weakestScore: number
  trend: number
}

export interface FilterOptions {
  reps: string[]
  channels: string[]
  models: string[]
  promptVersions: string[]
}

export interface OverviewFiltersState {
  dateFrom?: Date
  dateTo?: Date
}
