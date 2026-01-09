"use client"

import React from "react"
import { subDays } from "date-fns"
import { useAuth } from "@/app/auth/AuthContext"
import { OverviewFilters } from "@/components/ui/overview/OverviewFilters"
import { KpiGrid } from "@/components/ui/overview/KpiGrid"
import { SpinRadarCard } from "@/components/ui/overview/SpinRadarCard"
import { ModelHealthCard } from "@/components/ui/overview/ModelHealthCard"
import { SpinTrendCard } from "@/components/ui/overview/SpinTrendCard"
import { VolumeQualityTrendCard } from "@/components/ui/overview/VolumeQualityTrendCard"
import { CoachingQueueCard } from "@/components/ui/overview/CoachingQueueCard"
import { InsightsCard } from "@/components/ui/overview/InsightsCard"
import { RepLeaderboardCard } from "@/components/ui/overview/RepLeaderboardCard"
import { OverviewFiltersState, OverviewSummary, VolumeDataPoint, QueueItem, InsightItem, RepStats, ModelHealthData } from "@/types/overview"
import { fetchOverviewStatistics, fetchOverviewTrends, transformOverviewStatistics, TrendDataPoint, fetchCoachingQueue, fetchOverviewInsights, fetchRepLeaderboard, fetchModelHealth, transformModelHealth } from "@/lib/api"

export default function Overview() {
  const { accessToken } = useAuth()

  const [filters, setFilters] = React.useState<OverviewFiltersState>({
    dateFrom: subDays(new Date(), 30),
    dateTo: new Date(),
  })

  const [overviewData, setOverviewData] = React.useState<OverviewSummary | null>(null)
  const [trendData, setTrendData] = React.useState<TrendDataPoint[]>([])
  const [volumeData, setVolumeData] = React.useState<VolumeDataPoint[]>([])
  const [queueData, setQueueData] = React.useState<QueueItem[]>([])
  const [queueTotalCount, setQueueTotalCount] = React.useState(0)
  const [insights, setInsights] = React.useState<InsightItem[]>([])
  const [repStats, setRepStats] = React.useState<RepStats[]>([])
  const [modelHealthData, setModelHealthData] = React.useState<ModelHealthData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [trendLoading, setTrendLoading] = React.useState(true)
  const [queueLoading, setQueueLoading] = React.useState(true)
  const [insightsLoading, setInsightsLoading] = React.useState(true)
  const [repLeaderboardLoading, setRepLeaderboardLoading] = React.useState(true)
  const [modelHealthLoading, setModelHealthLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const fetchData = React.useCallback(async () => {
    if (!accessToken) return

    setLoading(true)
    setTrendLoading(true)
    setQueueLoading(true)
    setInsightsLoading(true)
    setRepLeaderboardLoading(true)
    setError(null)

    try {
      // Fetch aggregate statistics, trends, coaching queue, and insights in parallel
      const [statsResponse, trendsResponse, queueResponse, insightsResponse, leaderboardResponse] = await Promise.all([
        fetchOverviewStatistics({
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          includeDeltas: true,
          threshold: 3.5,
        }, accessToken),
        fetchOverviewTrends({
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
        }, accessToken),
        fetchCoachingQueue({
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          threshold: 3.5,
          limit: 10,
        }, accessToken),
        fetchOverviewInsights({
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          threshold: 3.5,
        }, accessToken),
        fetchRepLeaderboard({
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          limit: 15,
          includeTrend: true
        }, accessToken)
      ])

      const transformed = transformOverviewStatistics(statsResponse)
      setOverviewData(transformed)
      setTrendData(trendsResponse.trend_data)

      // Transform trend data for volume chart
      const volumeTransformed: VolumeDataPoint[] = trendsResponse.trend_data.map(point => ({
        date: point.date,
        count: point.conversation_count,
        percentAboveTarget: point.percent_above_target
      }))
      setVolumeData(volumeTransformed)

      // Transform coaching queue data
      const queueTransformed: QueueItem[] = queueResponse.items.map(item => ({
        id: item.id.toString(),
        rep: item.rep,
        buyer: item.buyer,
        composite: item.composite,
        weakestDim: item.weakest_dim,
        createdAt: item.created_at
      }))
      setQueueData(queueTransformed)
      setQueueTotalCount(queueResponse.total_count)
      setInsights(insightsResponse.insights)

      const leaderboardTransformed: RepStats[] = leaderboardResponse.items.map(item => ({
        rank: item.rank,
        rep: item.rep,
        conversationCount: item.conversation_count,
        avgComposite: item.avg_composite,
        strongest: item.strongest,
        strongestScore: item.strongest_score,
        weakest: item.weakest,
        weakestScore: item.weakest_score,
        trend: item.trend ?? 0
      }))
      setRepStats(leaderboardTransformed)
    } catch (err) {
      setQueueData([])
      setQueueTotalCount(0)
      setInsights([])
      setRepStats([])
      setError(err instanceof Error ? err.message : "Failed to load statistics")
      console.error("Overview statistics fetch error:", err)
    } finally {
      setLoading(false)
      setTrendLoading(false)
      setQueueLoading(false)
      setInsightsLoading(false)
      setRepLeaderboardLoading(false)
    }
  }, [filters, accessToken])

  React.useEffect(() => {
    fetchData()
  }, [fetchData])

  // Fetch model health independently on mount, not when filters change
  React.useEffect(() => {
    const fetchModelHealthData = async () => {
      if (!accessToken) return

      setModelHealthLoading(true)
      try {
        const response = await fetchModelHealth(accessToken)
        if (response) {
          setModelHealthData(transformModelHealth(response))
        } else {
          setModelHealthData(null)
        }
      } catch (err) {
        console.error("Model health fetch error:", err)
        setModelHealthData(null)
      } finally {
        setModelHealthLoading(false)
      }
    }

    fetchModelHealthData()
  }, [accessToken])  // Only depends on accessToken, NOT filters

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-50">
            Overview
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            SPIN scores, coaching workload, and model health at a glance
          </p>
        </div>
        <OverviewFilters
          filters={filters}
          onFiltersChange={setFilters}
        />
      </header>

      {/* KPI Summary Tiles */}
      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center">
          <p className="text-sm text-slate-600">Loading statistics...</p>
        </div>
      ) : error ? (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchData}
            className="text-sm font-medium text-red-700 hover:text-red-900 underline"
          >
            Retry
          </button>
        </div>
      ) : overviewData ? (
        <KpiGrid data={overviewData} />
      ) : (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center">
          <p className="text-sm text-slate-600">No conversations in selected date range</p>
        </div>
      )}

      {/* SPIN Radar + Model Health */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {loading ? (
          <div className="xl:col-span-2 rounded-lg border border-slate-800 bg-slate-900/70 p-6">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : overviewData?.dimensionAverages && overviewData.dimensionAverages.length > 0 ? (
          <SpinRadarCard
            data={overviewData.dimensionAverages}
            className="xl:col-span-2"
          />
        ) : (
          <div className="xl:col-span-2 rounded-lg border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="mb-2 text-lg font-semibold text-slate-200">SPIN profile (team average)</h3>
            <p className="text-sm text-slate-400">No SPIN data available for selected period</p>
          </div>
        )}
        {modelHealthLoading ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : modelHealthData ? (
          <ModelHealthCard healthData={modelHealthData} />
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h3 className="mb-2 text-sm font-medium text-slate-200">Model calibration</h3>
            <p className="text-xs text-slate-400">No evaluation data available. Run an evaluation to see model health metrics.</p>
          </div>
        )}
      </section>

      {/* Trends Charts */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {trendLoading ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : trendData.length > 0 ? (
          <SpinTrendCard trendData={trendData} />
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="mb-2 text-lg font-semibold text-slate-200">SPIN scores over time</h3>
            <p className="text-sm text-slate-400">No trend data available for selected period</p>
          </div>
        )}
        {trendLoading ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : volumeData.length > 0 ? (
          <VolumeQualityTrendCard volumeData={volumeData} />
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="mb-2 text-lg font-semibold text-slate-200">Volume & quality trend</h3>
            <p className="text-sm text-slate-400">No volume data available for selected period</p>
          </div>
        )}
      </section>

      {/* Coaching Queue + Insights */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {queueLoading ? (
          <div className="xl:col-span-2 rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : (
          <CoachingQueueCard queueData={queueData} totalCount={queueTotalCount} className="xl:col-span-2" />
        )}
        {insightsLoading ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
            <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
          </div>
        ) : insights.length > 0 ? (
          <InsightsCard insights={insights} />
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
            <h3 className="mb-2 text-lg font-semibold text-slate-200">This week&apos;s coaching insights</h3>
            <p className="text-sm text-slate-400">No insights available for the selected period.</p>
          </div>
        )}
      </section>

      {/* Rep Leaderboard */}
      {repLeaderboardLoading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="mb-2 h-5 w-48 animate-pulse rounded bg-slate-800"></div>
          <div className="h-4 w-64 animate-pulse rounded bg-slate-800"></div>
        </div>
      ) : repStats.length > 0 ? (
        <RepLeaderboardCard repStats={repStats} />
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
          <h3 className="mb-2 text-lg font-semibold text-slate-200">Rep leaderboard</h3>
          <p className="text-sm text-slate-400">No representative performance data available for the selected period.</p>
        </div>
      )}
    </div>
  )
}
