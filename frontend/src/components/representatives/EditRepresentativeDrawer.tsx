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
import { DatePicker } from "@/components/DatePicker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/Select";
import { updateRepresentative } from "@/lib/api";
import type { Representative, RepresentativeUpdate } from "@/types/representatives";
import { useAuth } from "@/app/auth/AuthContext";

interface Props {
  representative: Representative;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  departments: string[];
}

export function EditRepresentativeDrawer({
  representative,
  open,
  onOpenChange,
  onSuccess,
  departments,
}: Props) {
  const { accessToken } = useAuth();
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [hireDate, setHireDate] = React.useState<Date | undefined>(
    representative.hire_date ? new Date(representative.hire_date) : undefined
  );
  const [status, setStatus] = React.useState<string>(
    representative.is_active ? "active" : "inactive"
  );
  const [department, setDepartment] = React.useState<string>(
    representative.department || "none"
  );

  // Reset form when representative changes or drawer opens
  React.useEffect(() => {
    if (open) {
      setHireDate(
        representative.hire_date ? new Date(representative.hire_date) : undefined
      );
      setStatus(representative.is_active ? "active" : "inactive");
      setDepartment(representative.department || "none");
      setError(null);
    }
  }, [open, representative]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const form = e.currentTarget;
    const formData = new FormData(form);

    const data: RepresentativeUpdate = {
      email: formData.get("email") as string,
      full_name: formData.get("full_name") as string,
      department: department === "none" ? null : department,
      is_active: status === "active",
      hire_date: hireDate ? hireDate.toISOString() : null,
    };

    setSubmitting(true);
    try {
      await updateRepresentative(representative.id, data, accessToken);
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update representative"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="border-slate-800 bg-slate-950">
        <DrawerHeader>
          <DrawerTitle className="text-slate-100">
            Edit representative
          </DrawerTitle>
          <DrawerDescription className="text-slate-400">
            Update representative information and settings.
          </DrawerDescription>
        </DrawerHeader>

        <DrawerBody>
          <form id="edit-representative-form" onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md border border-rose-800 bg-rose-900/20 px-3 py-2 text-sm text-rose-300">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="full_name" className="text-sm font-medium text-slate-300">
                Full name <span className="text-rose-400">*</span>
              </Label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                defaultValue={representative.full_name}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="John Doe"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-slate-300">
                Email address <span className="text-rose-400">*</span>
              </Label>
              <input
                id="email"
                name="email"
                type="email"
                required
                defaultValue={representative.email}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="john.doe@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="department" className="text-sm font-medium text-slate-300">
                Department
              </Label>
              <Select 
                value={department} 
                onValueChange={setDepartment}
              >
                <SelectTrigger
                  id="department"
                  className="w-full border-slate-700 bg-slate-900 text-slate-100"
                >
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent className="border-slate-700 bg-slate-900">
                  <SelectItem value="none" className="text-slate-300">
                    None
                  </SelectItem>
                  {departments.map((dept) => (
                    <SelectItem
                      key={dept}
                      value={dept}
                      className="text-slate-300"
                    >
                      {dept}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status" className="text-sm font-medium text-slate-300">
                Status
              </Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger
                  id="status"
                  className="w-full border-slate-700 bg-slate-900 text-slate-100"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-slate-700 bg-slate-900">
                  <SelectItem value="active" className="text-slate-300">
                    Active
                  </SelectItem>
                  <SelectItem value="inactive" className="text-slate-300">
                    Inactive
                  </SelectItem>
                </SelectContent>
              </Select>
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
          </form>
        </DrawerBody>

        <DrawerFooter>
          <DrawerClose asChild>
            <Button variant="secondary" type="button">
              Cancel
            </Button>
          </DrawerClose>
          <Button
            variant="primary"
            type="submit"
            form="edit-representative-form"
            disabled={submitting}
          >
            {submitting ? "Saving..." : "Save"}
          </Button>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}

