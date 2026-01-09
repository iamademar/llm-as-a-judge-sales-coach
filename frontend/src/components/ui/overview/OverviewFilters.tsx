"use client"

import React from "react"
import { DatePicker } from "@/components/DatePicker"
import { OverviewFiltersState } from "@/types/overview"

interface OverviewFiltersProps {
  filters: OverviewFiltersState
  onFiltersChange: (filters: OverviewFiltersState) => void
}

export function OverviewFilters({
  filters,
  onFiltersChange,
}: OverviewFiltersProps) {
  const handleDateFromChange = (date?: Date) => {
    onFiltersChange({ ...filters, dateFrom: date })
  }

  const handleDateToChange = (date?: Date) => {
    onFiltersChange({ ...filters, dateTo: date })
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Date From */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">From:</span>
        <DatePicker
          value={filters.dateFrom}
          onChange={handleDateFromChange}
          placeholder="Start date"
        />
      </div>

      {/* Date To */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">To:</span>
        <DatePicker
          value={filters.dateTo}
          onChange={handleDateToChange}
          placeholder="End date"
        />
      </div>
    </div>
  )
}

