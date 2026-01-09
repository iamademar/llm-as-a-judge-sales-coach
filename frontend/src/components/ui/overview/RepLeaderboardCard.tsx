"use client"

import React from "react"
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
} from "@tanstack/react-table"
import { RepStats } from "@/types/overview"
import { RiTrophyLine } from "@remixicon/react"

interface RepLeaderboardCardProps {
  repStats: RepStats[]
  className?: string
}

export function RepLeaderboardCard({
  repStats,
  className = "",
}: RepLeaderboardCardProps) {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "avgComposite", desc: true },
  ])

  const columns: ColumnDef<RepStats>[] = [
    {
      accessorKey: "rank",
      header: "Rank",
      cell: ({ getValue }) => {
        const rank = getValue() as number
        return (
          <div className="flex items-center gap-2">
            {rank <= 3 && (
              <RiTrophyLine
                className={`h-4 w-4 ${
                  rank === 1
                    ? "text-yellow-400"
                    : rank === 2
                      ? "text-slate-400"
                      : "text-amber-600"
                }`}
              />
            )}
            <span className="text-slate-300">{rank}</span>
          </div>
        )
      },
    },
    {
      accessorKey: "rep",
      header: "Rep",
      cell: ({ getValue }) => (
        <span className="font-medium text-slate-200">{getValue() as string}</span>
      ),
    },
    {
      accessorKey: "conversationCount",
      header: "Conversations",
      cell: ({ getValue }) => (
        <span className="text-slate-300">{getValue() as number}</span>
      ),
    },
    {
      accessorKey: "avgComposite",
      header: "Avg SPIN",
      cell: ({ getValue }) => {
        const value = getValue() as number
        const color =
          value >= 3.5
            ? "text-emerald-400"
            : value >= 3
              ? "text-amber-400"
              : "text-rose-400"
        return <span className={`font-medium ${color}`}>{value.toFixed(1)}</span>
      },
    },
    {
      accessorKey: "strongest",
      header: "Strongest",
      cell: ({ row }) => (
        <div className="text-xs">
          <span className="text-slate-300">{row.original.strongest}</span>
          <span className="ml-1 text-emerald-400">
            ({row.original.strongestScore.toFixed(1)})
          </span>
        </div>
      ),
    },
    {
      accessorKey: "weakest",
      header: "Weakest",
      cell: ({ row }) => (
        <div className="text-xs">
          <span className="text-slate-300">{row.original.weakest}</span>
          <span className="ml-1 text-rose-400">
            ({row.original.weakestScore.toFixed(1)})
          </span>
        </div>
      ),
    },
    {
      accessorKey: "trend",
      header: "Trend",
      cell: ({ getValue }) => {
        const trend = getValue() as number
        const isPositive = trend > 0
        const isNeutral = trend === 0
        return (
          <span
            className={`inline-flex items-center gap-1 text-xs ${
              isNeutral
                ? "text-slate-400"
                : isPositive
                  ? "text-emerald-400"
                  : "text-rose-400"
            }`}
          >
            {isNeutral ? "—" : isPositive ? "↑" : "↓"}
            {!isNeutral && Math.abs(trend).toFixed(1)}
          </span>
        )
      },
    },
  ]

  const table = useReactTable({
    data: repStats,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  })

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3 ${className}`}
    >
      <h2 className="text-sm font-medium text-slate-200">Rep leaderboard</h2>
      <p className="text-xs text-slate-400">
        Performance ranking by average SPIN composite score
      </p>
      <div className="overflow-hidden rounded-lg border border-slate-800">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-3 py-2 text-left text-xs font-medium text-slate-400 cursor-pointer hover:text-slate-300"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-slate-800">
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-slate-800/60 cursor-pointer transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-3">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

