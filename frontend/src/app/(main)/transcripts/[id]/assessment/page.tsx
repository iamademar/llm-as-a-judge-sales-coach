"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/app/auth/AuthContext";
import {
  fetchTranscriptById,
  fetchAssessmentsByTranscript,
  fetchRepresentativeById,
} from "@/lib/api";
import type {
  Transcript,
  Assessment,
  Representative,
} from "@/types/representatives";
import { AssessmentHeader } from "@/components/assessments/AssessmentHeader";
import { OverallScoreCard } from "@/components/assessments/OverallScoreCard";
import { SpinScoresChart } from "@/components/assessments/SpinScoresChart";
import { QualityScoresRow } from "@/components/assessments/QualityScoresRow";
import { CoachingPanel } from "@/components/assessments/CoachingPanel";
import { TranscriptViewer } from "@/components/assessments/TranscriptViewer";
import { TechnicalMetaCard } from "@/components/assessments/TechnicalMetaCard";

export default function AssessmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();
  const transcriptId = Number(params.id);

  const [transcript, setTranscript] = React.useState<Transcript | null>(null);
  const [assessment, setAssessment] = React.useState<Assessment | null>(null);
  const [representative, setRepresentative] = React.useState<Representative | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchData() {
      if (!accessToken || isNaN(transcriptId)) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch transcript
        const transcriptData = await fetchTranscriptById(transcriptId, accessToken);
        setTranscript(transcriptData);

        // Fetch assessments for this transcript (get the latest one)
        const assessments = await fetchAssessmentsByTranscript(transcriptId, accessToken);
        if (assessments.length > 0) {
          // Sort by created_at descending and pick the latest
          const sorted = [...assessments].sort(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
          setAssessment(sorted[0]);
        }

        // Fetch representative if available
        if (transcriptData.representative_id) {
          try {
            const repData = await fetchRepresentativeById(
              transcriptData.representative_id,
              accessToken
            );
            setRepresentative(repData);
          } catch {
            // Representative fetch is optional, don't fail the whole page
            console.warn("Could not fetch representative data");
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [accessToken, transcriptId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-indigo-500 mx-auto" />
          <p className="text-sm text-slate-400">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error || !transcript) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-rose-400">{error || "Transcript not found"}</p>
          <button
            onClick={() => router.back()}
            className="mt-3 text-sm text-indigo-400 hover:text-indigo-300"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-amber-400">No assessment found for this transcript</p>
          <button
            onClick={() => router.back()}
            className="mt-3 text-sm text-indigo-400 hover:text-indigo-300"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">
      {/* Header */}
      <AssessmentHeader
        transcript={transcript}
        assessment={assessment}
        representative={representative}
        onBack={() => {
          if (representative) {
            router.push(`/representatives/${representative.id}`);
          } else {
            router.back();
          }
        }}
      />

      {/* Main Grid: Scores (left) + Coaching (right) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Scores */}
        <div className="space-y-6">
          <OverallScoreCard scores={assessment.scores} />
          <SpinScoresChart scores={assessment.scores} />
          <QualityScoresRow scores={assessment.scores} />
        </div>

        {/* Right Column: Coaching */}
        <div>
          <CoachingPanel coaching={assessment.coaching} />
        </div>
      </div>

      {/* Bottom Section: Transcript */}
      <TranscriptViewer transcript={transcript.transcript} />

      {/* Technical Meta */}
      <TechnicalMetaCard assessment={assessment} />
    </div>
  );
}

