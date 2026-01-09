"use client";

import * as React from "react";
import { RiCloseLine, RiUpload2Line, RiCheckLine } from "@remixicon/react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/Dialog";
import { Button } from "@/components/Button";
import { Label } from "@/components/Label";
import { assessTranscript, type AssessRequest, type AssessResponse } from "@/lib/api";
import { useAuth } from "@/app/auth/AuthContext";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  representativeId: string;
  representativeName?: string;
  onSuccess?: () => void;
}

type UploadState = "idle" | "uploading" | "success" | "error";

export function UploadTranscriptDialog({
  open,
  onOpenChange,
  representativeId,
  representativeName,
  onSuccess,
}: Props) {
  const { accessToken } = useAuth();
  const [state, setState] = React.useState<UploadState>("idle");
  const [error, setError] = React.useState<string | null>(null);
  const [file, setFile] = React.useState<File | null>(null);
  const [buyerId, setBuyerId] = React.useState("");
  const [assessmentResult, setAssessmentResult] = React.useState<AssessResponse | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Reset state when dialog opens/closes
  React.useEffect(() => {
    if (!open) {
      // Reset after animation completes
      const timeout = setTimeout(() => {
        setState("idle");
        setError(null);
        setFile(null);
        setBuyerId("");
        setAssessmentResult(null);
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [open]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    if (!accessToken) {
      setError("You must be signed in to upload transcripts");
      return;
    }

    setState("uploading");

    try {
      // Read file contents
      const transcript = await file.text();

      if (!transcript.trim()) {
        throw new Error("File is empty");
      }

      // Prepare metadata
      const metadata: Record<string, string> = {
        representative_id: representativeId,
      };
      
      if (buyerId.trim()) {
        metadata.buyer_id = buyerId.trim();
      }

      // Call assess API
      const data: AssessRequest = {
        transcript,
        metadata,
      };

      const result = await assessTranscript(data, accessToken);
      setAssessmentResult(result);
      setState("success");
      
      // Call success callback after a short delay
      setTimeout(() => {
        onSuccess?.();
      }, 1500);
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Failed to assess transcript");
    }
  };

  const calculateAverageScore = (scores: AssessResponse["scores"]): number => {
    const { situation, problem, implication, need_payoff, flow, tone, engagement } = scores;
    return (situation + problem + implication + need_payoff + flow + tone + engagement) / 7;
  };

  const getScoreColor = (score: number): string => {
    if (score >= 4) return "text-emerald-400";
    if (score >= 3) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-slate-800 bg-slate-950 sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-lg font-semibold text-slate-100">
              Upload Transcript
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
            {representativeName
              ? `Upload and analyze a conversation for ${representativeName}`
              : "Upload and analyze a conversation transcript"}
          </DialogDescription>
        </DialogHeader>

        {state === "success" && assessmentResult ? (
          // Success view
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-center gap-2 rounded-lg border border-emerald-800 bg-emerald-900/20 px-4 py-3">
              <RiCheckLine className="h-5 w-5 text-emerald-400" />
              <span className="text-sm font-medium text-emerald-300">
                Transcript analyzed successfully!
              </span>
            </div>

            {/* Scores Display */}
            <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
              <h3 className="text-sm font-semibold text-slate-100">SPIN Scores</h3>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Average Score</p>
                  <p className={`text-2xl font-bold ${getScoreColor(calculateAverageScore(assessmentResult.scores))}`}>
                    {calculateAverageScore(assessmentResult.scores).toFixed(1)}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Assessment ID</p>
                  <p className="text-sm font-mono text-slate-300">
                    #{assessmentResult.assessment_id}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
                {Object.entries(assessmentResult.scores).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className={`font-semibold ${getScoreColor(value)}`}>
                      {value}/5
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Coaching Summary */}
            {assessmentResult.coaching.summary && (
              <div className="space-y-2 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                <h3 className="text-sm font-semibold text-slate-100">Coaching Summary</h3>
                <p className="text-sm text-slate-300">
                  {assessmentResult.coaching.summary}
                </p>
              </div>
            )}

            <div className="flex items-center justify-end pt-4">
              <Button
                variant="primary"
                onClick={() => onOpenChange(false)}
              >
                Done
              </Button>
            </div>
          </div>
        ) : (
          // Upload form
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            {error && (
              <div className="rounded-md border border-rose-800 bg-rose-900/20 px-3 py-2 text-sm text-rose-300">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="file" className="text-sm font-medium text-slate-300">
                Transcript file <span className="text-rose-400">*</span>
              </Label>
              <div className="flex items-center gap-2">
                <input
                  ref={fileInputRef}
                  id="file"
                  name="file"
                  type="file"
                  accept=".txt,.json"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={state === "uploading"}
                />
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={state === "uploading"}
                  className="w-full justify-start"
                >
                  <RiUpload2Line className="h-4 w-4 mr-2" />
                  {file ? file.name : "Choose file (.txt, .json)"}
                </Button>
              </div>
              {file && (
                <p className="text-xs text-slate-400">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="buyer_id" className="text-sm font-medium text-slate-300">
                Buyer/Customer ID
              </Label>
              <input
                id="buyer_id"
                name="buyer_id"
                type="text"
                value={buyerId}
                onChange={(e) => setBuyerId(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Optional customer identifier"
                disabled={state === "uploading"}
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-4">
              <DialogClose asChild>
                <Button variant="secondary" type="button" disabled={state === "uploading"}>
                  Cancel
                </Button>
              </DialogClose>
              <Button
                variant="primary"
                type="submit"
                disabled={state === "uploading" || !file}
              >
                {state === "uploading" ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-100 border-t-transparent mr-2" />
                    Analyzing...
                  </>
                ) : (
                  "Upload & Analyze"
                )}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

