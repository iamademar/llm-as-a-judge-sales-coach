"use client";

import * as React from "react";
import { RiMore2Fill, RiEyeLine, RiEditLine } from "@remixicon/react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuIconWrapper,
} from "@/components/Dropdown";
import type { Representative } from "@/types/representatives";

type DrawerMode = "view" | "edit" | null;

interface Props {
  representative: Representative;
  onOpenDrawer: (mode: DrawerMode) => void;
}

export function RepresentativeActionsMenu({
  representative: _representative,
  onOpenDrawer,
}: Props) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="inline-flex items-center justify-center rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        onClick={(e) => e.stopPropagation()}
      >
        <RiMore2Fill className="h-5 w-5" aria-hidden="true" />
        <span className="sr-only">Open actions menu</span>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="w-48 border-slate-700 bg-slate-900"
      >
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onOpenDrawer("view");
          }}
        >
          <DropdownMenuIconWrapper>
            <RiEyeLine className="h-4 w-4" aria-hidden="true" />
          </DropdownMenuIconWrapper>
          <span>View details</span>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onOpenDrawer("edit");
          }}
        >
          <DropdownMenuIconWrapper>
            <RiEditLine className="h-4 w-4" aria-hidden="true" />
          </DropdownMenuIconWrapper>
          <span>Edit</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator className="border-slate-700" />

        <DropdownMenuItem disabled>
          <span className="text-slate-500">Deactivate</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

