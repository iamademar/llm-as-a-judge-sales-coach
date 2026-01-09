"use client";

import * as React from "react";
import { RiSearchLine } from "@remixicon/react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/Select";
import { DateRangePicker, DateRange } from "@/components/DatePicker";

export interface FilterState {
  search: string;
  department: string | null;
  status: "all" | "active" | "inactive";
  hireDateRange: DateRange | undefined;
}

interface Props {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  departments: string[]; // List of unique departments for the dropdown
}

export function RepresentativesFilters({
  filters,
  onFiltersChange,
  departments,
}: Props) {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ ...filters, search: e.target.value });
  };

  const handleDepartmentChange = (value: string) => {
    onFiltersChange({
      ...filters,
      department: value === "all" ? null : value,
    });
  };

  const handleStatusChange = (value: string) => {
    onFiltersChange({
      ...filters,
      status: value as "all" | "active" | "inactive",
    });
  };

  const handleDateRangeChange = (range: DateRange | undefined) => {
    onFiltersChange({ ...filters, hireDateRange: range });
  };

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-3">
      {/* Search */}
      <div className="relative flex-1">
        <RiSearchLine className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={filters.search}
          onChange={handleSearchChange}
          placeholder="Search by name or email..."
          className="w-full rounded-md border border-slate-700 bg-slate-900 pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      {/* Department Filter */}
      <div className="w-full sm:w-48">
        <Select
          value={filters.department || "all"}
          onValueChange={handleDepartmentChange}
        >
          <SelectTrigger className="w-full border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800">
            <SelectValue placeholder="All departments" />
          </SelectTrigger>
          <SelectContent className="border-slate-700 bg-slate-900">
            <SelectItem value="all" className="text-slate-100">
              All departments
            </SelectItem>
            {departments.map((dept) => (
              <SelectItem key={dept} value={dept} className="text-slate-100">
                {dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Status Filter */}
      <div className="w-full sm:w-40">
        <Select value={filters.status} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-full border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800">
            <SelectValue placeholder="All status" />
          </SelectTrigger>
          <SelectContent className="border-slate-700 bg-slate-900">
            <SelectItem value="all" className="text-slate-100">
              All status
            </SelectItem>
            <SelectItem value="active" className="text-slate-100">
              Active
            </SelectItem>
            <SelectItem value="inactive" className="text-slate-100">
              Inactive
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Hire Date Range */}
      <div className="w-full sm:w-64">
        <DateRangePicker
          value={filters.hireDateRange}
          onChange={handleDateRangeChange}
          placeholder="Hire date range"
          className="w-full border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
        />
      </div>
    </div>
  );
}

