"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  useReactTable,
  ColumnDef,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
  ColumnFiltersState,
} from "@tanstack/react-table";
import { twMerge } from "tailwind-merge";
import {
  RiMoreLine,
  RiEyeLine,
  RiRefreshLine,
  RiArrowUpSLine,
  RiArrowDownSLine,
} from "@remixicon/react";
import { Input } from "@/components/Input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/Select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/Dropdown";
import { Button } from "@/components/Button";
import type { Transcript, Assessment } from "@/types/representatives";

interface TranscriptRow {
  id: number;
  buyerId: string;
  createdAt: string;
  spinScore: number | null;
  status: "completed" | "pending";
  transcript: Transcript;
  assessment: Assessment | null;
}

interface Props {
  transcripts: Transcript[];
  assessments: Assessment[];
  onRefresh: () => void;
}

export function TranscriptsTable({ transcripts, assessments, onRefresh: _onRefresh }: Props) {
  const router = useRouter();
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "createdAt", desc: true },
  ]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");

  // Navigate to assessment detail page
  const navigateToAssessment = React.useCallback(
    (transcriptId: number) => {
      router.push(`/transcripts/${transcriptId}/assessment`);
    },
    [router]
  );

  // Calculate composite SPIN score from assessment scores
  const calculateCompositeScore = (scores: Assessment["scores"]): number => {
    const {
      situation,
      problem,
      implication,
      need_payoff,
      flow,
      tone,
      engagement,
    } = scores;
    return (
      (situation + problem + implication + need_payoff + flow + tone + engagement) /
      7
    );
  };

  // Transform data for the table
  const tableData: TranscriptRow[] = React.useMemo(() => {
    const assessmentMap = new Map(assessments.map((a) => [a.transcript_id, a]));

    return transcripts.map((t) => {
      const assessment = assessmentMap.get(t.id) || null;
      return {
        id: t.id,
        buyerId: t.buyer_id || "Unknown",
        createdAt: t.created_at,
        spinScore: assessment ? calculateCompositeScore(assessment.scores) : null,
        status: assessment ? "completed" : "pending",
        transcript: t,
        assessment,
      };
    });
  }, [transcripts, assessments]);

  // Filter by status
  const filteredData = React.useMemo(() => {
    if (statusFilter === "all") return tableData;
    return tableData.filter((row) => row.status === statusFilter);
  }, [tableData, statusFilter]);

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-slate-500";
    if (score >= 3.5) return "text-emerald-400";
    if (score >= 3) return "text-amber-300";
    return "text-rose-400";
  };

  const getScoreBgColor = (score: number | null) => {
    if (score === null) return "bg-slate-800";
    if (score >= 3.5) return "bg-emerald-900/40";
    if (score >= 3) return "bg-amber-900/40";
    return "bg-rose-900/40";
  };

  const columns = React.useMemo<ColumnDef<TranscriptRow>[]>(
    () => [
      {
        accessorKey: "createdAt",
        header: ({ column }) => {
          const isSorted = column.getIsSorted();
          return (
            <button
              className="flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-200"
              onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            >
              Date / Time
              {isSorted === "asc" && <RiArrowUpSLine className="h-4 w-4" />}
              {isSorted === "desc" && <RiArrowDownSLine className="h-4 w-4" />}
            </button>
          );
        },
        cell: ({ getValue }) => {
          const date = new Date(getValue<string>());
          return (
            <div className="text-sm">
              <div className="text-slate-200">
                {date.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </div>
              <div className="text-xs text-slate-500">
                {date.toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "buyerId",
        header: () => (
          <span className="text-xs font-medium text-slate-400">Buyer / Customer</span>
        ),
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-200">{getValue<string>()}</span>
        ),
        filterFn: "includesString",
      },
      {
        accessorKey: "spinScore",
        header: ({ column }) => {
          const isSorted = column.getIsSorted();
          return (
            <button
              className="flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-200"
              onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            >
              SPIN Score
              {isSorted === "asc" && <RiArrowUpSLine className="h-4 w-4" />}
              {isSorted === "desc" && <RiArrowDownSLine className="h-4 w-4" />}
            </button>
          );
        },
        cell: ({ getValue }) => {
          const score = getValue<number | null>();
          return (
            <span
              className={twMerge(
                "inline-flex items-center rounded-md px-2 py-1 text-sm font-medium",
                getScoreBgColor(score),
                getScoreColor(score)
              )}
            >
              {score !== null ? score.toFixed(2) : "—"}
            </span>
          );
        },
        sortingFn: (rowA, rowB) => {
          const a = rowA.getValue<number | null>("spinScore");
          const b = rowB.getValue<number | null>("spinScore");
          if (a === null && b === null) return 0;
          if (a === null) return 1;
          if (b === null) return -1;
          return a - b;
        },
      },
      {
        accessorKey: "status",
        header: () => (
          <span className="text-xs font-medium text-slate-400">Status</span>
        ),
        cell: ({ getValue }) => {
          const status = getValue<"completed" | "pending">();
          return (
            <span
              className={twMerge(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                status === "completed"
                  ? "bg-emerald-900/40 text-emerald-300"
                  : "bg-amber-900/40 text-amber-300"
              )}
            >
              {status === "completed" ? "Completed" : "Pending"}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const { assessment, transcript } = row.original;

          return (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                  onClick={(e) => e.stopPropagation()}
                >
                  <RiMoreLine className="h-4 w-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="border-slate-800 bg-slate-950"
              >
                <DropdownMenuItem
                  className="text-slate-200 hover:bg-slate-800"
                  disabled={!assessment}
                  onClick={() => {
                    if (assessment) {
                      navigateToAssessment(transcript.id);
                    }
                  }}
                >
                  <RiEyeLine className="mr-2 h-4 w-4" />
                  View Assessment
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-slate-200 hover:bg-slate-800"
                  onClick={() => {
                    // TODO: Re-run analysis
                    console.log("Re-run analysis for transcript:", transcript.id);
                  }}
                >
                  <RiRefreshLine className="mr-2 h-4 w-4" />
                  Re-run Analysis
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
      },
    ],
    [navigateToAssessment]
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-4">
          <Input
            type="search"
            placeholder="Search by buyer ID..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="max-w-xs"
            inputClassName="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-500"
          />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px] border-slate-800 bg-slate-950 text-slate-100">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent className="border-slate-800 bg-slate-950">
              <SelectItem value="all" className="text-slate-200 hover:bg-slate-800">
                All Status
              </SelectItem>
              <SelectItem value="completed" className="text-slate-200 hover:bg-slate-800">
                Completed
              </SelectItem>
              <SelectItem value="pending" className="text-slate-200 hover:bg-slate-800">
                Pending
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="text-sm text-slate-400">
          {filteredData.length} conversation{filteredData.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-800">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => {
                const hasAssessment = row.original.assessment !== null;
                return (
                  <tr
                    key={row.id}
                    className={twMerge(
                      "transition-colors hover:bg-slate-900/60",
                      hasAssessment && "cursor-pointer"
                    )}
                    onClick={() => {
                      if (hasAssessment) {
                        navigateToAssessment(row.original.transcript.id);
                      }
                    }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3 align-middle">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-slate-500"
                >
                  No conversations found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

