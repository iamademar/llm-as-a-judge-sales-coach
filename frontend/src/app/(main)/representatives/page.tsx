"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/auth/AuthContext";
import { RepresentativesTable } from "@/components/representatives/RepresentativesTable";
import {
  RepresentativesFilters,
  FilterState,
} from "@/components/representatives/RepresentativesFilters";
import { AddRepresentativeDialog } from "@/components/representatives/AddRepresentativeDialog";
import { EditRepresentativeDrawer } from "@/components/representatives/EditRepresentativeDrawer";
import { ViewRepresentativeDrawer } from "@/components/representatives/ViewRepresentativeDrawer";
import { UploadTranscriptDialog } from "@/components/representatives/UploadTranscriptDialog";
import {
  fetchRepresentatives,
  fetchTranscripts,
  fetchAssessments,
} from "@/lib/api";
import type {
  Representative,
  Transcript,
  Assessment,
  RepresentativeRow,
} from "@/types/representatives";

type DrawerMode = "view" | "edit" | null;

// Threshold for determining if a transcript should be in the queue
const QUEUE_THRESHOLD = 3.0;

export default function RepresentativesPage() {
  const { accessToken } = useAuth();
  const router = useRouter();

  const [representatives, setRepresentatives] = React.useState<Representative[]>([]);
  const [transcripts, setTranscripts] = React.useState<Transcript[]>([]);
  const [assessments, setAssessments] = React.useState<Assessment[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [filters, setFilters] = React.useState<FilterState>({
    search: "",
    department: null,
    status: "all",
    hireDateRange: undefined,
  });

  const [selectedRepresentative, setSelectedRepresentative] =
    React.useState<Representative | null>(null);
  const [drawerMode, setDrawerMode] = React.useState<DrawerMode>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = React.useState(false);
  const [uploadRepresentative, setUploadRepresentative] = React.useState<Representative | null>(null);

  // Fetch all data
  const fetchData = React.useCallback(async () => {
    if (!accessToken) return;

    setLoading(true);
    setError(null);

    try {
      const [repsData, transcriptsData, assessmentsData] = await Promise.all([
        fetchRepresentatives(accessToken),
        fetchTranscripts(null, accessToken),
        fetchAssessments(null, accessToken),
      ]);

      setRepresentatives(repsData);
      setTranscripts(transcriptsData);
      setAssessments(assessmentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  // Aggregate data for table
  const aggregatedData: RepresentativeRow[] = React.useMemo(() => {
    return representatives.map((rep) => {
      // Get transcripts for this rep
      const repTranscripts = transcripts.filter(
        (t) => t.representative_id === rep.id
      );

      // Get assessments for those transcripts
      const repAssessments = assessments.filter((a) =>
        repTranscripts.some((t) => t.id === a.transcript_id)
      );

      // Calculate avg SPIN score
      let avgSpinScore: number | null = null;
      if (repAssessments.length > 0) {
        const total = repAssessments.reduce(
          (sum, a) => sum + calculateCompositeScore(a.scores),
          0
        );
        avgSpinScore = total / repAssessments.length;
      }

      // Calculate queue count (transcripts with score < threshold)
      const queueCount = repAssessments.filter(
        (a) => calculateCompositeScore(a.scores) < QUEUE_THRESHOLD
      ).length;

      // Get last transcript timestamp
      const lastTranscriptAt =
        repTranscripts.length > 0
          ? repTranscripts
              .map((t) => new Date(t.created_at).getTime())
              .reduce((max, ts) => Math.max(max, ts), 0)
          : null;

      return {
        id: rep.id,
        fullName: rep.full_name,
        email: rep.email,
        department: rep.department,
        isActive: rep.is_active,
        hireDate: rep.hire_date,
        createdAt: rep.created_at,
        transcriptCount: repTranscripts.length,
        lastTranscriptAt: lastTranscriptAt
          ? new Date(lastTranscriptAt).toISOString()
          : null,
        avgSpinScore,
        queueCount,
      };
    });
  }, [representatives, transcripts, assessments]);

  // Filter data
  const filteredData = React.useMemo(() => {
    return aggregatedData.filter((row) => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesSearch =
          row.fullName.toLowerCase().includes(searchLower) ||
          row.email.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Department filter
      if (filters.department) {
        if (row.department !== filters.department) return false;
      }

      // Status filter
      if (filters.status === "active" && !row.isActive) return false;
      if (filters.status === "inactive" && row.isActive) return false;

      // Hire date range filter
      if (filters.hireDateRange?.from && row.hireDate) {
        const hireDate = new Date(row.hireDate);
        const fromDate = new Date(filters.hireDateRange.from);
        if (hireDate < fromDate) return false;
      }
      if (filters.hireDateRange?.to && row.hireDate) {
        const hireDate = new Date(row.hireDate);
        const toDate = new Date(filters.hireDateRange.to);
        // Set to end of day for inclusive comparison
        toDate.setHours(23, 59, 59, 999);
        if (hireDate > toDate) return false;
      }

      return true;
    });
  }, [aggregatedData, filters]);

  // Get unique departments for filter dropdown
  const departments = React.useMemo(() => {
    const deptSet = new Set<string>();
    representatives.forEach((rep) => {
      if (rep.department) {
        deptSet.add(rep.department);
      }
    });
    return Array.from(deptSet).sort();
  }, [representatives]);

  const handleUploadClick = (repId: string) => {
    const rep = representatives.find((r) => r.id === repId);
    if (rep) {
      setUploadRepresentative(rep);
      setUploadDialogOpen(true);
    }
  };

  const handleRowClick = (repId: string) => {
    router.push(`/representatives/${repId}`);
  };

  const handleOpenDrawer = (representative: Representative, mode: DrawerMode) => {
    setSelectedRepresentative(representative);
    setDrawerMode(mode);
  };

  const handleCloseDrawer = () => {
    setDrawerMode(null);
    setSelectedRepresentative(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-indigo-500 mx-auto" />
          <p className="text-sm text-slate-400">Loading representatives...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-rose-400">{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 text-sm text-indigo-400 hover:text-indigo-300"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">
            Representatives
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage reps and create transcripts for SPIN assessments.
          </p>
        </div>
        <AddRepresentativeDialog onSuccess={fetchData} />
      </div>

      {/* Filters */}
      <RepresentativesFilters
        filters={filters}
        onFiltersChange={setFilters}
        departments={departments}
      />

      {/* Stats Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs font-medium text-slate-400">Total Reps</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">
            {filteredData.length}
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs font-medium text-slate-400">Active</p>
          <p className="mt-1 text-2xl font-semibold text-emerald-400">
            {filteredData.filter((r) => r.isActive).length}
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs font-medium text-slate-400">Total Conversations</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">
            {filteredData.reduce((sum, r) => sum + r.transcriptCount, 0)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs font-medium text-slate-400">In Queue</p>
          <p className="mt-1 text-2xl font-semibold text-amber-400">
            {filteredData.reduce((sum, r) => sum + r.queueCount, 0)}
          </p>
        </div>
      </div>

      {/* Table */}
      {filteredData.length === 0 ? (
        <div className="flex min-h-[300px] items-center justify-center rounded-xl border border-slate-800 bg-slate-950/60">
          <div className="text-center">
            <p className="text-sm text-slate-400">
              {filters.search || filters.department || filters.status !== "all"
                ? "No representatives match your filters"
                : "No representatives yet. Add one to get started."}
            </p>
          </div>
        </div>
      ) : (
        <RepresentativesTable
          data={filteredData}
          representatives={representatives}
          onUploadClick={handleUploadClick}
          onRowClick={handleRowClick}
          onOpenDrawer={handleOpenDrawer}
          departments={departments}
        />
      )}

      {/* Edit Drawer */}
      {selectedRepresentative && (
        <EditRepresentativeDrawer
          representative={selectedRepresentative}
          open={drawerMode === "edit"}
          onOpenChange={(open) => {
            if (!open) handleCloseDrawer();
          }}
          onSuccess={fetchData}
          departments={departments}
        />
      )}

      {/* View Drawer */}
      {selectedRepresentative && (
        <ViewRepresentativeDrawer
          representative={selectedRepresentative}
          open={drawerMode === "view"}
          onOpenChange={(open) => {
            if (!open) handleCloseDrawer();
          }}
        />
      )}

      {/* Upload Transcript Dialog */}
      {uploadRepresentative && (
        <UploadTranscriptDialog
          open={uploadDialogOpen}
          onOpenChange={setUploadDialogOpen}
          representativeId={uploadRepresentative.id}
          representativeName={uploadRepresentative.full_name}
          onSuccess={fetchData}
        />
      )}
    </div>
  );
}

