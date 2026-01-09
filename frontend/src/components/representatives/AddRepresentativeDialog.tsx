"use client";

import * as React from "react";
import { RiAddLine, RiCloseLine } from "@remixicon/react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/Dialog";
import { Button } from "@/components/Button";
import { Label } from "@/components/Label";
import { DatePicker } from "@/components/DatePicker";
import { createRepresentative } from "@/lib/api";
import type { RepresentativeCreate } from "@/types/representatives";
import { useAuth } from "@/app/auth/AuthContext";

interface Props {
  onSuccess?: () => void;
}

export function AddRepresentativeDialog({ onSuccess }: Props) {
  const { accessToken } = useAuth();
  const [open, setOpen] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [hireDate, setHireDate] = React.useState<Date | undefined>(undefined);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const form = e.currentTarget;
    const formData = new FormData(form);

    const data: RepresentativeCreate = {
      email: formData.get("email") as string,
      full_name: formData.get("full_name") as string,
      department: (formData.get("department") as string) || null,
      hire_date: hireDate ? hireDate.toISOString() : null,
    };

    setSubmitting(true);
    try {
      await createRepresentative(data, accessToken);
      form.reset();
      setHireDate(undefined);
      setOpen(false);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create representative");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="primary" className="inline-flex items-center gap-2">
          <RiAddLine className="h-4 w-4" />
          Add representative
        </Button>
      </DialogTrigger>

      <DialogContent className="border-slate-800 bg-slate-950 sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-lg font-semibold text-slate-100">
              Add representative
            </DialogTitle>
            <DialogClose asChild>
              <button
                type="button"
                className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                aria-label="Close"
              >
                <RiCloseLine className="h-5 w-5" />
              </button>
            </DialogClose>
          </div>
          <DialogDescription className="text-sm text-slate-400">
            Create a new sales representative profile for tracking conversations
            and assessments.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {error && (
            <div className="rounded-md border border-rose-800 bg-rose-900/20 px-3 py-2 text-sm text-rose-300">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium text-slate-300">
              Email address <span className="text-rose-400">*</span>
            </Label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="john.doe@example.com"
            />
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="full_name"
              className="text-sm font-medium text-slate-300"
            >
              Full name <span className="text-rose-400">*</span>
            </Label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              required
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="John Doe"
            />
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="department"
              className="text-sm font-medium text-slate-300"
            >
              Department
            </Label>
            <input
              id="department"
              name="department"
              type="text"
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Sales, Marketing, etc."
            />
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium text-slate-300">
              Hire date
            </Label>
            <DatePicker
              value={hireDate}
              onChange={setHireDate}
              placeholder="Select hire date"
              className="w-full border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-4">
            <DialogClose asChild>
              <Button variant="secondary" type="button">
                Cancel
              </Button>
            </DialogClose>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? "Creating..." : "Create representative"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

