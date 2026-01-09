/**
 * TypeScript types for representatives, transcripts, and assessments.
 * 
 * These types match the backend Pydantic schemas.
 */

// Representative types
export interface Representative {
  id: string;                       // UUID as string
  email: string;
  full_name: string;
  department: string | null;
  is_active: boolean;
  hire_date: string | null;         // ISO datetime string
  created_at: string;               // ISO datetime string
}

export interface RepresentativeCreate {
  email: string;
  full_name: string;
  department?: string | null;
  hire_date?: string | null;        // ISO datetime string
}

export interface RepresentativeUpdate {
  email?: string;
  full_name?: string;
  department?: string | null;
  is_active?: boolean;
  hire_date?: string | null;        // ISO datetime string
}

// Transcript types
export interface Transcript {
  id: number;
  representative_id: string | null;  // UUID as string
  buyer_id: string | null;
  metadata: Record<string, any> | null;
  transcript: string;
  created_at: string;                // ISO datetime string
}

export interface TranscriptCreate {
  representative_id?: string | null;
  buyer_id?: string | null;
  metadata?: Record<string, any> | null;
  transcript: string;
}

// Assessment types
export interface AssessmentScores {
  situation: number;     // 1-5
  problem: number;       // 1-5
  implication: number;   // 1-5
  need_payoff: number;   // 1-5
  flow: number;          // 1-5
  tone: number;          // 1-5
  engagement: number;    // 1-5
}

export interface AssessmentCoaching {
  summary: string;
  wins: string[];
  gaps: string[];
  next_actions: string[];
}

export interface Assessment {
  id: number;
  transcript_id: number;
  scores: AssessmentScores;
  coaching: AssessmentCoaching;
  model_name: string;
  prompt_version: string;
  latency_ms: number | null;
  created_at: string;    // ISO datetime string
}

// Aggregated view for table display
export interface RepresentativeRow {
  id: string;                       // representatives.id
  fullName: string;                 // representatives.full_name
  email: string;                    // representatives.email
  department: string | null;        // representatives.department
  isActive: boolean;                // representatives.is_active
  hireDate: string | null;          // representatives.hire_date
  createdAt: string;                // representatives.created_at
  transcriptCount: number;          // COUNT(transcripts.id)
  lastTranscriptAt: string | null;  // MAX(transcripts.created_at)
  avgSpinScore: number | null;      // AVG over assessments.scores composite
  queueCount: number;               // # of transcripts where latest assessment composite < threshold
}

// Helper type for transcript with its latest assessment
export interface TranscriptWithAssessment {
  transcript: Transcript;
  latestAssessment: Assessment | null;
}

