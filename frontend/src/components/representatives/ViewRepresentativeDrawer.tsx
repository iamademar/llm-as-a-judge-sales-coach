"use client";

import * as React from "react";
import {
  Drawer,
  DrawerBody,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/Drawer";
import { Button } from "@/components/Button";
import { Label } from "@/components/Label";
import type { Representative } from "@/types/representatives";

interface Props {
  representative: Representative;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ViewRepresentativeDrawer({
  representative,
  open,
  onOpenChange,
}: Props) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "—";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="border-slate-800 bg-slate-950">
        <DrawerHeader>
          <DrawerTitle className="text-slate-100">
            Representative details
          </DrawerTitle>
          <DrawerDescription className="text-slate-400">
            View representative information and metadata.
          </DrawerDescription>
        </DrawerHeader>

        <DrawerBody>
          <div className="space-y-5">
            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Full name
              </Label>
              <p className="mt-1 text-sm text-slate-100">
                {representative.full_name}
              </p>
            </div>

            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Email address
              </Label>
              <p className="mt-1 text-sm text-slate-100">
                {representative.email}
              </p>
            </div>

            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Department
              </Label>
              <p className="mt-1 text-sm text-slate-100">
                {representative.department || "—"}
              </p>
            </div>

            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Status
              </Label>
              <p className="mt-1">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                    representative.is_active
                      ? "bg-emerald-900/40 text-emerald-300"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {representative.is_active ? "Active" : "Inactive"}
                </span>
              </p>
            </div>

            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Hire date
              </Label>
              <p className="mt-1 text-sm text-slate-100">
                {formatDate(representative.hire_date)}
              </p>
            </div>

            <div className="border-t border-slate-800 pt-4">
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Record ID
              </Label>
              <p className="mt-1 font-mono text-xs text-slate-400">
                {representative.id}
              </p>
            </div>

            <div>
              <Label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Created at
              </Label>
              <p className="mt-1 text-sm text-slate-100">
                {formatDate(representative.created_at)}
              </p>
            </div>
          </div>
        </DrawerBody>

        <DrawerFooter>
          <DrawerClose asChild>
            <Button variant="secondary" type="button">
              Close
            </Button>
          </DrawerClose>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}

