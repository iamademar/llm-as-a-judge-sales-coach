"use client";

import * as React from "react";
import { useReactTable, ColumnDef, getCoreRowModel, flexRender } from "@tanstack/react-table";
import { twMerge } from "tailwind-merge";
import { RiUpload2Line, RiUserLine } from "@remixicon/react";
import * as Checkbox from "@radix-ui/react-checkbox";
import { RiCheckLine } from "@remixicon/react";
import type { RepresentativeRow, Representative } from "@/types/representatives";
import { RepresentativeActionsMenu } from "./RepresentativeActionsMenu";

type DrawerMode = "view" | "edit" | null;

type Props = {
  data: RepresentativeRow[];
  representatives: Representative[];
  onUploadClick: (id: string) => void;
  onRowClick?: (id: string) => void;
  onOpenDrawer: (representative: Representative, mode: DrawerMode) => void;
  departments: string[];
};

export function RepresentativesTable({
  data,
  representatives,
  onUploadClick,
  onRowClick,
  onOpenDrawer,
  departments: _departments,
}: Props) {
  const columns = React.useMemo<ColumnDef<RepresentativeRow>[]>(
    () => [
      {
        id: "select",
        header: () => (
          <Checkbox.Root
            className="flex h-4 w-4 items-center justify-center rounded border border-slate-600 bg-slate-900 data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
          >
            <Checkbox.Indicator>
              <RiCheckLine className="h-3 w-3 text-white" />
            </Checkbox.Indicator>
          </Checkbox.Root>
        ),
        cell: () => (
          <Checkbox.Root className="flex h-4 w-4 items-center justify-center rounded border border-slate-600 bg-slate-900 data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500">
            <Checkbox.Indicator>
              <RiCheckLine className="h-3 w-3 text-white" />
            </Checkbox.Indicator>
          </Checkbox.Root>
        ),
      },
      {
        accessorKey: "fullName",
        header: "Representative",
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 text-xs text-slate-200">
              <RiUserLine className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-medium text-slate-100">
                {row.original.fullName}
              </div>
              <div className="text-xs text-slate-400">{row.original.email}</div>
            </div>
          </div>
        ),
      },
      {
        accessorKey: "department",
        header: "Department",
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-300">
            {(getValue() as string) ?? "—"}
          </span>
        ),
      },
      {
        accessorKey: "isActive",
        header: "Status",
        cell: ({ getValue }) => {
          const active = getValue<boolean>();
          return (
            <span
              className={twMerge(
                "inline-flex items-center rounded-full px-2 py-0.5 text-xs",
                active
                  ? "bg-emerald-900/40 text-emerald-300"
                  : "bg-slate-800 text-slate-300",
              )}
            >
              {active ? "Active" : "Inactive"}
            </span>
          );
        },
      },
      {
        accessorKey: "transcriptCount",
        header: "Conversations",
        cell: ({ getValue }) => (
          <span className="text-sm text-slate-200">
            {getValue<number>().toLocaleString()}
          </span>
        ),
      },
      {
        accessorKey: "avgSpinScore",
        header: "Avg SPIN",
        cell: ({ getValue }) => {
          const score = getValue<number | null>();
          if (score == null) return <span className="text-xs text-slate-500">—</span>;

          const color =
            score >= 3.5
              ? "text-emerald-400"
              : score >= 3
              ? "text-amber-300"
              : "text-rose-400";

          return (
            <span className={twMerge("text-sm font-medium", color)}>
              {score.toFixed(1)}
            </span>
          );
        },
      },
      {
        accessorKey: "queueCount",
        header: "Queue",
        cell: ({ getValue }) => {
          const count = getValue<number>();
          if (!count) return <span className="text-xs text-slate-500">0</span>;
          return (
            <span className="inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-amber-900/40 px-2 py-0.5 text-xs text-amber-300">
              {count}
            </span>
          );
        },
      },
      {
        accessorKey: "lastTranscriptAt",
        header: "Last transcript",
        cell: ({ getValue }) => {
          const v = getValue<string | null>();
          return (
            <span className="text-xs text-slate-400">
              {v ? new Date(v).toLocaleString() : "—"}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const representative = representatives.find(
            (rep) => rep.id === row.original.id
          );
          if (!representative) return null;

          return (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onUploadClick(row.original.id);
                }}
                className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100 hover:bg-slate-800"
              >
                <RiUpload2Line className="h-3 w-3" />
                Upload
              </button>
              <RepresentativeActionsMenu
                representative={representative}
                onOpenDrawer={(mode) => onOpenDrawer(representative, mode)}
              />
            </div>
          );
        },
      },
    ],
    [onUploadClick, representatives, onOpenDrawer],
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-900/80">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-3 py-2 text-left text-xs font-medium text-slate-400"
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
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="cursor-pointer hover:bg-slate-900/60"
              onClick={() => onRowClick?.(row.original.id)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 align-middle">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

