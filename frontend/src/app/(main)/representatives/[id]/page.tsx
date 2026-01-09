"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { RiArrowLeftLine } from "@remixicon/react";
import { useAuth } from "@/app/auth/AuthContext";
import { Button } from "@/components/Button";
import { RepDetailTabs } from "@/components/representatives/RepDetailTabs";
import {
  fetchRepresentativeById,
  fetchTranscripts,
  fetchAssessments,
} from "@/lib/api";
import type {
  Representative,
  Transcript,
  Assessment,
} from "@/types/representatives";

export default function RepresentativeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();
  const repId = params.id as string;

  const [representative, setRepresentative] = React.useState<Representative | null>(null);
  const [transcripts, setTranscripts] = React.useState<Transcript[]>([]);
  const [assessments, setAssessments] = React.useState<Assessment[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchData = React.useCallback(async () => {
    if (!accessToken || !repId) return;

    setLoading(true);
    setError(null);

    try {
      const [repData, transcriptsData, assessmentsData] = await Promise.all([
        fetchRepresentativeById(repId, accessToken),
        fetchTranscripts(repId, accessToken),
        fetchAssessments(null, accessToken),
      ]);

      setRepresentative(repData);
      setTranscripts(transcriptsData);
      setAssessments(assessmentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [accessToken, repId]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-indigo-500 mx-auto" />
          <p className="text-sm text-slate-400">Loading representative...</p>
        </div>
      </div>
    );
  }

  if (error || !representative) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-rose-400">{error || "Representative not found"}</p>
          <button
            onClick={() => router.push("/representatives")}
            className="mt-3 text-sm text-indigo-400 hover:text-indigo-300"
          >
            Back to Representatives
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="p-2"
          onClick={() => router.push("/representatives")}
        >
          <RiArrowLeftLine className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">
            {representative.full_name}
          </h1>
          <p className="text-sm text-slate-400">{representative.email}</p>
        </div>
        <span
          className={`ml-auto inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
            representative.is_active
              ? "bg-emerald-900/40 text-emerald-300"
              : "bg-slate-800 text-slate-300"
          }`}
        >
          {representative.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {/* Tabs */}
      <RepDetailTabs
        representative={representative}
        transcripts={transcripts}
        assessments={assessments}
        onRefresh={fetchData}
      />
    </div>
  );
}

