'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchSeedStatus, triggerSeed } from '@/lib/api';
import type { SeedStatusResponse, SeedTriggerResponse } from '@/types/seed';

export default function SeedStatusPage() {
  const [status, setStatus] = useState<SeedStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSeedStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load seed status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      setError(null);
      setSuccessMessage(null);
      const result: SeedTriggerResponse = await triggerSeed();

      // Show success message with summary
      setSuccessMessage(
        `Successfully deleted ${result.summary.organizations_deleted} orgs, ` +
        `${result.summary.users_deleted} users, ` +
        `${result.summary.representatives_deleted} reps, ` +
        `${result.summary.transcripts_deleted} transcripts, ` +
        `${result.summary.assessments_deleted} assessments. ` +
        `Created ${result.summary.organizations_created} orgs, ` +
        `${result.summary.representatives_created} reps, ` +
        `${result.summary.transcripts_created} transcripts, ` +
        `${result.summary.assessments_created} assessments ` +
        `in ${result.summary.duration_seconds.toFixed(1)}s.`
      );

      // Refresh status
      await loadStatus();
      setShowConfirm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger seed');
    } finally {
      setSeeding(false);
    }
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get badge color based on seeding level
  const getBadgeColor = (level: string) => {
    switch (level) {
      case 'full':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'partial':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'none':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-indigo-500" />
              <p className="text-slate-400">Loading seed status...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="min-h-screen bg-slate-950 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="rounded-lg border border-red-800 bg-red-950/50 p-6">
            <p className="text-sm text-red-400">{error}</p>
            <button
              onClick={loadStatus}
              className="mt-4 rounded bg-red-800 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Demo Data Seeding</h1>
          <p className="mt-2 text-slate-400">
            View and manage demo data for testing and demonstrations
          </p>
        </div>

        {/* Status Badge */}
        {status && (
          <div>
            <span
              className={`inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium ${getBadgeColor(
                status.seeding_level
              )}`}
            >
              {status.seeding_level === 'none' && 'Not Seeded'}
              {status.seeding_level === 'partial' && 'Partially Seeded'}
              {status.seeding_level === 'full' && '✓ Fully Seeded'}
            </span>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="rounded-lg border border-emerald-800 bg-emerald-950/50 p-4">
            <p className="text-sm text-emerald-400">{successMessage}</p>
          </div>
        )}

        {/* Error Message */}
        {error && status && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 p-4">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        {status && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
              <div className="text-4xl font-bold text-slate-100">
                {status.totals.organizations}
              </div>
              <div className="mt-1 text-sm text-slate-400">Organizations</div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
              <div className="text-4xl font-bold text-slate-100">
                {status.totals.representatives}
              </div>
              <div className="mt-1 text-sm text-slate-400">Representatives</div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
              <div className="text-4xl font-bold text-slate-100">
                {status.totals.transcripts.toLocaleString()}
              </div>
              <div className="mt-1 text-sm text-slate-400">Transcripts</div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
              <div className="text-4xl font-bold text-slate-100">
                {status.totals.assessments.toLocaleString()}
              </div>
              <div className="mt-1 text-sm text-slate-400">Assessments</div>
            </div>
          </div>
        )}

        {/* Organizations Breakdown */}
        {status && status.organizations.length > 0 && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-lg font-semibold text-slate-100 mb-4">
              Organizations
            </h2>
            <div className="space-y-3">
              {status.organizations.map((org) => (
                <div
                  key={org.id}
                  className="flex items-center justify-between rounded border border-slate-800 bg-slate-950 p-3"
                >
                  <span className="text-slate-100">
                    {org.is_demo_org && '🎭 '}
                    {org.name}
                  </span>
                  <span className="text-sm text-slate-400">
                    {org.rep_count} reps · {org.transcript_count} calls
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Date Range */}
        {status && status.date_range && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <p className="text-sm text-slate-400">
              <span className="font-medium">Date Range:</span>{' '}
              {formatDate(status.date_range.earliest)} -{' '}
              {formatDate(status.date_range.latest)}
            </p>
          </div>
        )}

        {/* Warning and Seed Button */}
        {status && (
          <div className="space-y-4">
            {status.is_seeded && (
              <div className="rounded-lg border border-amber-800 bg-amber-950/50 p-4">
                <p className="text-sm text-amber-400">
                  ⚠️ <strong>WARNING:</strong> Seeding will DELETE ALL existing data
                  (all organizations, users, representatives, transcripts, and assessments)
                  and create fresh demo data.
                </p>
              </div>
            )}

            <button
              onClick={() => setShowConfirm(true)}
              disabled={seeding}
              className="rounded bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-700 disabled:bg-slate-700 disabled:text-slate-500"
            >
              {seeding ? 'Seeding...' : 'Seed Demo Data'}
            </button>
          </div>
        )}

        {/* Confirmation Dialog */}
        {showConfirm && status && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-lg rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-xl">
              <h2 className="text-xl font-bold text-slate-100 mb-4">
                ⚠️ Delete All Data and Reseed?
              </h2>

              <div className="mb-4 rounded-lg border border-red-800 bg-red-950/50 p-4">
                <p className="font-bold text-red-400 mb-2">
                  This will permanently delete ALL existing data:
                </p>
                <ul className="ml-6 list-disc space-y-1 text-red-400">
                  <li>All organizations ({status.totals.organizations})</li>
                  <li>All users</li>
                  <li>All representatives ({status.totals.representatives})</li>
                  <li>All transcripts ({status.totals.transcripts})</li>
                  <li>All assessments ({status.totals.assessments})</li>
                </ul>
                <p className="mt-3 font-bold text-red-400">
                  Fresh demo data will be created after deletion.
                </p>
              </div>

              <p className="mb-6 text-slate-300">
                This action cannot be undone. Are you sure?
              </p>

              <div className="flex gap-3">
                <button
                  onClick={handleSeed}
                  disabled={seeding}
                  className="flex-1 rounded bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 disabled:bg-slate-700 disabled:text-slate-500"
                >
                  {seeding ? 'Deleting & Seeding...' : 'Delete All & Reseed'}
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  disabled={seeding}
                  className="flex-1 rounded border border-slate-700 bg-slate-800 px-4 py-2 font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
