/**
 * TypeScript types for seed management.
 *
 * Mirrors the backend Pydantic schemas for type safety.
 */

export interface OrganizationSeedInfo {
  id: string;
  name: string;
  rep_count: number;
  transcript_count: number;
  is_demo_org: boolean;
}

export interface SeedTotals {
  organizations: number;
  representatives: number;
  transcripts: number;
  assessments: number;
}

export interface DateRange {
  earliest: string;
  latest: string;
}

export interface SeedStatusResponse {
  is_seeded: boolean;
  seeding_level: 'none' | 'partial' | 'full';
  organizations: OrganizationSeedInfo[];
  totals: SeedTotals;
  date_range: DateRange | null;
}

export interface SeedSummary {
  organizations_deleted: number;
  representatives_deleted: number;
  transcripts_deleted: number;
  assessments_deleted: number;
  users_deleted: number;
  organizations_created: number;
  representatives_created: number;
  transcripts_created: number;
  assessments_created: number;
  duration_seconds: number;
}

export interface SeedTriggerResponse {
  success: boolean;
  message: string;
  summary: SeedSummary;
}
