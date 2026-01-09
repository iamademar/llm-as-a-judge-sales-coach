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
import { QueueItem } from "@/types/overview"

interface CoachingQueueCardProps {
  queueData: QueueItem[]
  totalCount?: number
  className?: string
}

export function CoachingQueueCard({
  queueData,
  totalCount,
  className = "",
}: CoachingQueueCardProps) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const conversationsNeedingReview = totalCount ?? queueData.length

  const columns: ColumnDef<QueueItem>[] = [
    {
      accessorKey: "rep",
      header: "Rep",
      cell: ({ getValue }) => (
        <span className="text-slate-200">{getValue() as string}</span>
      ),
    },
    {
      accessorKey: "buyer",
      header: "Buyer / Account",
      cell: ({ getValue }) => (
        <span className="text-slate-200">{getValue() as string}</span>
      ),
    },
    {
      accessorKey: "composite",
      header: "SPIN",
      cell: ({ getValue }) => {
        const value = getValue() as number
        const color =
          value >= 3.5
            ? "text-emerald-400"
            : value >= 3
              ? "text-amber-400"
              : "text-rose-400"
        return <span className={color}>{value.toFixed(1)}</span>
      },
    },
    {
      accessorKey: "weakestDim",
      header: "Weakest area",
      cell: ({ getValue }) => (
        <span className="text-slate-300">{getValue() as string}</span>
      ),
    },
    {
      accessorKey: "createdAt",
      header: "Analyzed",
      cell: ({ getValue }) => {
        const date = new Date(getValue() as string)
        return (
          <span className="text-xs text-slate-400">
            {date.toLocaleDateString()} {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )
      },
    },
  ]

  const table = useReactTable({
    data: queueData,
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
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-200">Coaching queue</h2>
        <span className="text-xs text-slate-400">
          {conversationsNeedingReview} conversation{conversationsNeedingReview !== 1 ? "s" : ""} need review
        </span>
      </div>
      <p className="text-xs text-slate-400">
        Conversations scoring below 3.5 requiring coaching attention
      </p>
      {queueData.length === 0 ? (
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-6 text-center text-sm text-slate-400">
          No conversations fell below the threshold for this time range.
        </div>
      ) : (
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
                    onClick={() => {
                      // Placeholder for navigation
                      console.log("Navigate to conversation:", row.original.id)
                    }}
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
      )}
    </div>
  )
}
