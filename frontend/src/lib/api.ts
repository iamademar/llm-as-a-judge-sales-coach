/**
 * API Client Library
 *
 * Provides a token-aware fetch helper for making authenticated requests
 * to both the backend API and Next.js API routes.
 */

import type {
  Representative,
  RepresentativeCreate,
  RepresentativeUpdate,
  Transcript,
  TranscriptCreate,
  Assessment,
  AssessmentScores,
  AssessmentCoaching,
} from '@/types/representatives';
import type { OverviewSummary, SpinRadarData, ModelHealthData } from '@/types/overview';
import type { SeedStatusResponse, SeedTriggerResponse } from '@/types/seed';

// Backend API base URL
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

/**
 * Token-aware fetch helper
 *
 * @param path - API path (relative to API_BASE for backend calls, or full path for Next.js routes)
 * @param opts - Fetch options
 * @param token - Optional JWT access token for Authorization header
 * @returns Fetch response
 */
export async function apiFetch(
  path: string,
  opts: RequestInit = {},
  token?: string | null
): Promise<Response> {
  // Prepare headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string>),
  };

  // Add Authorization header if token is provided
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Determine full URL
  const url = path.startsWith('http') || path.startsWith('/api')
    ? path
    : `${API_BASE}${path}`;

  // Make request with credentials included for cookie support
  return fetch(url, {
    ...opts,
    headers,
    credentials: 'include', // Important: includes httpOnly cookies
  });
}

/**
 * Fetch all representatives
 *
 * @param token - Optional JWT access token
 * @returns Array of representatives
 */
export async function fetchRepresentatives(
  token?: string | null
): Promise<Representative[]> {
  const response = await apiFetch('/representatives', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch representatives: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single representative by ID
 *
 * @param id - Representative UUID
 * @param token - Optional JWT access token
 * @returns Representative data
 */
export async function fetchRepresentativeById(
  id: string,
  token?: string | null
): Promise<Representative> {
  const response = await apiFetch(`/representatives/${id}`, {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch representative: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new representative
 *
 * @param data - Representative creation data
 * @param token - Optional JWT access token
 * @returns Created representative
 */
export async function createRepresentative(
  data: RepresentativeCreate,
  token?: string | null
): Promise<Representative> {
  const response = await apiFetch(
    '/representatives',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    throw new Error(`Failed to create representative: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update an existing representative
 *
 * @param id - Representative UUID
 * @param data - Representative update data (partial)
 * @param token - Optional JWT access token
 * @returns Updated representative
 */
export async function updateRepresentative(
  id: string,
  data: RepresentativeUpdate,
  token?: string | null
): Promise<Representative> {
  const response = await apiFetch(
    `/representatives/${id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update representative: ${errorText || response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch all transcripts, optionally filtered by representative
 *
 * @param representativeId - Optional representative UUID to filter by
 * @param token - Optional JWT access token
 * @returns Array of transcripts
 */
export async function fetchTranscripts(
  representativeId?: string | null,
  token?: string | null
): Promise<Transcript[]> {
  const params = new URLSearchParams();
  if (representativeId) {
    params.set('representative_id', representativeId);
  }
  
  const path = `/transcripts${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch transcripts: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new transcript
 *
 * @param data - Transcript creation data
 * @param token - Optional JWT access token
 * @returns Created transcript
 */
export async function createTranscript(
  data: TranscriptCreate,
  token?: string | null
): Promise<Transcript> {
  const response = await apiFetch(
    '/transcripts',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    throw new Error(`Failed to create transcript: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch all assessments, optionally filtered by transcript
 *
 * @param transcriptId - Optional transcript ID to filter by
 * @param token - Optional JWT access token
 * @returns Array of assessments
 */
export async function fetchAssessments(
  transcriptId?: number | null,
  token?: string | null
): Promise<Assessment[]> {
  const params = new URLSearchParams();
  if (transcriptId !== null && transcriptId !== undefined) {
    params.set('transcript_id', transcriptId.toString());
  }
  
  const path = `/assess${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch assessments: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single transcript by ID
 *
 * @param id - Transcript ID
 * @param token - Optional JWT access token
 * @returns Transcript data
 */
export async function fetchTranscriptById(
  id: number,
  token?: string | null
): Promise<Transcript> {
  const response = await apiFetch(`/transcripts/${id}`, {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch transcript: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch assessments for a specific transcript
 *
 * @param transcriptId - Transcript ID
 * @param token - Optional JWT access token
 * @returns Array of assessments for the transcript
 */
export async function fetchAssessmentsByTranscript(
  transcriptId: number,
  token?: string | null
): Promise<Assessment[]> {
  const response = await apiFetch(`/assess/by-transcript/${transcriptId}`, {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch assessments: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Request type for assessment endpoint
 */
export interface AssessRequest {
  transcript: string;
  metadata: Record<string, string>;
}

/**
 * Response type for assessment endpoint
 */
export interface AssessResponse {
  assessment_id: number;
  scores: AssessmentScores;
  coaching: AssessmentCoaching;
}

/**
 * Assess a transcript using the SPIN framework
 *
 * @param data - Assessment request data with transcript and metadata
 * @param token - JWT access token for authentication
 * @returns Assessment response with scores and coaching
 */
export async function assessTranscript(
  data: AssessRequest,
  token?: string | null
): Promise<AssessResponse> {
  const response = await apiFetch(
    '/assess',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to assess transcript: ${errorText || response.statusText}`);
  }
  
  return response.json();
}

// ============================================================================
// LLM Credentials API
// ============================================================================

/**
 * Supported LLM providers
 */
export type LLMProvider = 'openai' | 'anthropic' | 'google';

/**
 * Provider information for display
 */
export interface ProviderInfo {
  id: string;
  name: string;
  description: string;
  default_model: string;
  key_prefix: string;
  docs_url: string;
}

/**
 * LLM credential response from API
 */
export interface LLMCredential {
  id: string;
  organization_id: string;
  provider: LLMProvider;
  masked_key: string;
  default_model: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * LLM credentials list response
 */
export interface LLMCredentialListResponse {
  credentials: LLMCredential[];
  providers: ProviderInfo[];
}

/**
 * Request to create a new LLM credential
 */
export interface LLMCredentialCreate {
  provider: LLMProvider;
  api_key: string;
  default_model?: string;
}

/**
 * Request to update an LLM credential
 */
export interface LLMCredentialUpdate {
  api_key?: string;
  default_model?: string;
  is_active?: boolean;
}

/**
 * Fetch all LLM credentials for the current organization
 *
 * @param token - JWT access token
 * @returns Credentials list with provider info
 */
export async function fetchLLMCredentials(
  token?: string | null
): Promise<LLMCredentialListResponse> {
  const response = await apiFetch('/llm-credentials', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch LLM credentials: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch available LLM providers
 *
 * @param token - JWT access token
 * @returns List of available providers
 */
export async function fetchLLMProviders(
  token?: string | null
): Promise<{ providers: ProviderInfo[] }> {
  const response = await apiFetch('/llm-credentials/providers', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch LLM providers: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new LLM credential
 *
 * @param data - Credential creation data
 * @param token - JWT access token
 * @returns Created credential
 */
export async function createLLMCredential(
  data: LLMCredentialCreate,
  token?: string | null
): Promise<LLMCredential> {
  const response = await apiFetch(
    '/llm-credentials',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Update an existing LLM credential
 *
 * @param id - Credential UUID
 * @param data - Credential update data
 * @param token - JWT access token
 * @returns Updated credential
 */
export async function updateLLMCredential(
  id: string,
  data: LLMCredentialUpdate,
  token?: string | null
): Promise<LLMCredential> {
  const response = await apiFetch(
    `/llm-credentials/${id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Delete an LLM credential
 *
 * @param id - Credential UUID
 * @param token - JWT access token
 */
export async function deleteLLMCredential(
  id: string,
  token?: string | null
): Promise<void> {
  const response = await apiFetch(
    `/llm-credentials/${id}`,
    {
      method: 'DELETE',
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
}

// ============================================================================
// Prompt Templates API
// ============================================================================

/**
 * Prompt template response from API
 */
export interface PromptTemplate {
  id: string;
  organization_id: string;
  name: string;
  version: string;
  system_prompt: string;
  user_template: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Request to create a new prompt template
 */
export interface PromptTemplateCreate {
  name: string;
  version?: string;
  system_prompt: string;
  user_template: string;
  is_active?: boolean;
}

/**
 * Request to update a prompt template
 */
export interface PromptTemplateUpdate {
  name?: string;
  version?: string;
  system_prompt?: string;
  user_template?: string;
  is_active?: boolean;
}

/**
 * Prompt template preview response
 */
export interface PromptTemplatePreview {
  system_prompt: string;
  user_prompt: string;
  transcript_sample: string;
}

/**
 * Fetch all prompt templates for the current organization
 *
 * @param token - JWT access token
 * @returns Array of prompt templates
 */
export async function fetchPromptTemplates(
  token?: string | null
): Promise<PromptTemplate[]> {
  const response = await apiFetch('/prompt-templates', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch prompt templates: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch the active prompt template for the current organization
 *
 * @param token - JWT access token
 * @returns Active prompt template
 */
export async function fetchActivePromptTemplate(
  token?: string | null
): Promise<PromptTemplate> {
  const response = await apiFetch('/prompt-templates/active', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch active template: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch the default prompt template values (hardcoded defaults)
 *
 * @param token - JWT access token
 * @returns Preview with default system_prompt and user_template
 */
export async function fetchPromptTemplateDefaults(
  token?: string | null
): Promise<PromptTemplatePreview> {
  const response = await apiFetch('/prompt-templates/defaults', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch defaults: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new prompt template
 *
 * @param data - Template creation data
 * @param token - JWT access token
 * @returns Created template
 */
export async function createPromptTemplate(
  data: PromptTemplateCreate,
  token?: string | null
): Promise<PromptTemplate> {
  const response = await apiFetch(
    '/prompt-templates',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Update an existing prompt template
 *
 * @param id - Template UUID
 * @param data - Template update data
 * @param token - JWT access token
 * @returns Updated template
 */
export async function updatePromptTemplate(
  id: string,
  data: PromptTemplateUpdate,
  token?: string | null
): Promise<PromptTemplate> {
  const response = await apiFetch(
    `/prompt-templates/${id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Activate a prompt template (sets it as the active one for the org)
 *
 * @param id - Template UUID
 * @param token - JWT access token
 * @returns Activated template
 */
export async function activatePromptTemplate(
  id: string,
  token?: string | null
): Promise<PromptTemplate> {
  const response = await apiFetch(
    `/prompt-templates/${id}/activate`,
    {
      method: 'POST',
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Preview how a template renders with a sample transcript
 *
 * @param data - Template data to preview
 * @param token - JWT access token
 * @returns Preview with rendered prompts
 */
export async function previewPromptTemplate(
  data: PromptTemplateCreate,
  token?: string | null
): Promise<PromptTemplatePreview> {
  const response = await apiFetch(
    '/prompt-templates/preview',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Delete a prompt template
 *
 * @param id - Template UUID
 * @param token - JWT access token
 */
export async function deletePromptTemplate(
  id: string,
  token?: string | null
): Promise<void> {
  const response = await apiFetch(
    `/prompt-templates/${id}`,
    {
      method: 'DELETE',
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
}

// ==================== EVALUATION TYPES ====================

export interface EvaluationDataset {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  source_type: 'csv' | 'langsmith' | 'database';
  source_path: string | null;
  num_examples: number;
  langsmith_dataset_name?: string;
  langsmith_dataset_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationDatasetCreate {
  name: string;
  description?: string;
  file: File;
}

export interface EvaluationDatasetUpdate {
  name?: string;
  description?: string;
  source_path?: string;
}

export interface EvaluationRun {
  id: string;
  prompt_template_id: string;
  dataset_id: string | null;
  experiment_name: string | null;
  num_examples: number;
  macro_pearson_r: number | null;
  macro_qwk: number | null;
  macro_plus_minus_one: number | null;
  per_dimension_metrics: Record<string, {
    pearson_r: number;
    qwk: number;
    plus_minus_one_accuracy: number;
  }>;
  model_name: string | null;
  runtime_seconds: number | null;
  langsmith_url?: string;
  langsmith_experiment_id?: string;
  created_at: string;
}

export interface RunEvaluationRequest {
  prompt_template_id: string;
  dataset_id: string;
  experiment_name?: string;
}

// ==================== EVALUATION API FUNCTIONS ====================

/**
 * Fetch all evaluation datasets for the current organization
 *
 * @param token - JWT access token
 * @returns Array of evaluation datasets
 */
export async function fetchEvaluationDatasets(
  token?: string | null
): Promise<EvaluationDataset[]> {
  const response = await apiFetch('/evaluations/datasets', {}, token);
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new evaluation dataset with file upload
 *
 * @param data - Dataset creation data with file
 * @param token - JWT access token
 * @returns Created dataset
 */
export async function createEvaluationDataset(
  data: EvaluationDatasetCreate,
  token?: string | null
): Promise<EvaluationDataset> {
  const formData = new FormData();
  formData.append('name', data.name);
  if (data.description) {
    formData.append('description', data.description);
  }
  formData.append('file', data.file);

  // For file uploads, we need to handle headers differently
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // Don't set Content-Type - let browser set it with boundary for multipart

  const url = `${API_BASE}/evaluations/datasets`;
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Update an evaluation dataset
 *
 * @param id - Dataset UUID
 * @param data - Dataset update data
 * @param token - JWT access token
 * @returns Updated dataset
 */
export async function updateEvaluationDataset(
  id: string,
  data: EvaluationDatasetUpdate,
  token?: string | null
): Promise<EvaluationDataset> {
  const response = await apiFetch(
    `/evaluations/datasets/${id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Delete an evaluation dataset
 *
 * @param id - Dataset UUID
 * @param token - JWT access token
 */
export async function deleteEvaluationDataset(
  id: string,
  token?: string | null
): Promise<void> {
  const response = await apiFetch(
    `/evaluations/datasets/${id}`,
    {
      method: 'DELETE',
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
}

/**
 * Fetch all evaluation runs for a specific prompt template
 *
 * @param templateId - Template UUID
 * @param token - JWT access token
 * @returns Array of evaluation runs
 */
export async function fetchTemplateEvaluations(
  templateId: string,
  token?: string | null
): Promise<EvaluationRun[]> {
  const response = await apiFetch(
    `/evaluations/templates/${templateId}/runs`,
    {},
    token
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch evaluations: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Run an evaluation for a prompt template
 *
 * @param data - Evaluation request data
 * @param token - JWT access token
 * @returns Created evaluation run
 */
export async function runEvaluation(
  data: RunEvaluationRequest,
  token?: string | null
): Promise<EvaluationRun> {
  const response = await apiFetch(
    '/evaluations/run',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || response.statusText);
  }
  return response.json();
}

/**
 * Fetch a specific evaluation run by ID
 *
 * @param runId - Run UUID
 * @param token - JWT access token
 * @returns Evaluation run data
 */
export async function fetchEvaluationRun(
  runId: string,
  token?: string | null
): Promise<EvaluationRun> {
  const response = await apiFetch(
    `/evaluations/runs/${runId}`,
    {},
    token
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch evaluation run: ${response.statusText}`);
  }
  return response.json();
}

// ==================== OVERVIEW STATISTICS ====================

/**
 * Overview statistics response from API
 */
export interface OverviewStatistics {
  total_conversations: number;
  avg_composite_score: number;
  percentage_above_target: number;
  weakest_dimension: string;
  dimension_averages: Record<string, number>;
  delta_conversations: string | null;
  delta_score: string | null;
  delta_percentage: string | null;
}

/**
 * Fetch overview statistics for the dashboard
 *
 * @param params - Filter parameters (date range, threshold, deltas)
 * @param token - JWT access token
 * @returns Overview statistics
 */
export async function fetchOverviewStatistics(
  params: {
    dateFrom?: Date;
    dateTo?: Date;
    threshold?: number;
    includeDeltas?: boolean;
  },
  token?: string | null
): Promise<OverviewStatistics> {
  // Build query parameters
  const queryParams = new URLSearchParams();
  
  if (params.dateFrom) {
    queryParams.set('date_from', params.dateFrom.toISOString());
  }
  
  if (params.dateTo) {
    queryParams.set('date_to', params.dateTo.toISOString());
  }
  
  if (params.threshold !== undefined) {
    queryParams.set('threshold', params.threshold.toString());
  }
  
  if (params.includeDeltas !== undefined) {
    queryParams.set('include_deltas', params.includeDeltas.toString());
  }
  
  const path = `/overview/statistics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch overview statistics: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Time-series trend data point (matches backend TrendDataPoint)
 */
export interface TrendDataPoint {
  date: string;
  situation: number;
  problem: number;
  implication: number;
  need_payoff: number;
  flow: number;
  tone: number;
  engagement: number;
  conversation_count: number;
  percent_above_target: number;
}

/**
 * Overview trends response from API
 */
export interface OverviewTrendsResponse {
  trend_data: TrendDataPoint[];
  total_days: number;
  days_with_data: number;
}

/**
 * Fetch time-series SPIN dimension trends for the dashboard
 *
 * @param params - Filter parameters (date range)
 * @param token - JWT access token
 * @returns Time-series trend data
 */
export async function fetchOverviewTrends(
  params: {
    dateFrom?: Date;
    dateTo?: Date;
  },
  token?: string | null
): Promise<OverviewTrendsResponse> {
  // Build query parameters
  const queryParams = new URLSearchParams();
  queryParams.set('timeseries', 'true');

  if (params.dateFrom) {
    queryParams.set('date_from', params.dateFrom.toISOString());
  }

  if (params.dateTo) {
    queryParams.set('date_to', params.dateTo.toISOString());
  }

  const path = `/overview/statistics?${queryParams.toString()}`;
  const response = await apiFetch(path, {}, token);

  if (!response.ok) {
    throw new Error(`Failed to fetch overview trends: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Transform API response from snake_case to camelCase
 *
 * @param data - Raw API response with snake_case keys
 * @returns Transformed data with camelCase keys matching OverviewSummary
 */
export function transformOverviewStatistics(data: OverviewStatistics): OverviewSummary {
  // Transform dimension_averages to SpinRadarData format
  const dimensionAverages: SpinRadarData[] | undefined =
    data.dimension_averages && Object.keys(data.dimension_averages).length > 0
      ? formatDimensionAverages(data.dimension_averages)
      : undefined;

  return {
    totalConversations: data.total_conversations,
    avgCompositeScore: data.avg_composite_score,
    percentageAboveTarget: data.percentage_above_target,
    weakestDimension: data.weakest_dimension,
    dimensionAverages,
    ...(data.delta_conversations && { deltaConversations: data.delta_conversations }),
    ...(data.delta_score && { deltaScore: data.delta_score }),
    ...(data.delta_percentage && { deltaPercentage: data.delta_percentage }),
  };
}

/**
 * Format dimension averages from backend format to SpinRadarData format
 *
 * @param averages - Dictionary of dimension averages from backend
 * @returns Array of SpinRadarData for radar chart
 */
function formatDimensionAverages(averages: Record<string, number>): SpinRadarData[] {
  // Define dimension order to match radar chart expectations
  const dimensionOrder = [
    { key: 'situation', label: 'Situation' },
    { key: 'problem', label: 'Problem' },
    { key: 'implication', label: 'Implication' },
    { key: 'need_payoff', label: 'Need-payoff' },
    { key: 'flow', label: 'Flow' },
    { key: 'tone', label: 'Tone' },
    { key: 'engagement', label: 'Engagement' },
  ];

  return dimensionOrder
    .map(({ key, label }) => ({
      dimension: label,
      value: averages[key] || 0
    }))
    .filter(d => d.value !== undefined);
}

// ==================== COACHING QUEUE ====================

/**
 * Coaching queue item from API
 */
export interface CoachingQueueItem {
  id: number;
  rep: string;
  buyer: string;
  composite: number;
  weakest_dim: string;
  created_at: string;
}

/**
 * Coaching queue response from API
 */
export interface CoachingQueueResponse {
  items: CoachingQueueItem[];
  total_count: number;
}

/**
 * Fetch coaching queue for the dashboard
 *
 * @param params - Filter parameters (date range, threshold, limit)
 * @param token - JWT access token
 * @returns Coaching queue items
 */
export async function fetchCoachingQueue(
  params: {
    dateFrom?: Date;
    dateTo?: Date;
    threshold?: number;
    limit?: number;
  },
  token?: string | null
): Promise<CoachingQueueResponse> {
  // Build query parameters
  const queryParams = new URLSearchParams();

  if (params.dateFrom) {
    queryParams.set('date_from', params.dateFrom.toISOString());
  }

  if (params.dateTo) {
    queryParams.set('date_to', params.dateTo.toISOString());
  }

  if (params.threshold !== undefined) {
    queryParams.set('threshold', params.threshold.toString());
  }

  if (params.limit !== undefined) {
    queryParams.set('limit', params.limit.toString());
  }

  const path = `/overview/coaching-queue${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);

  if (!response.ok) {
    throw new Error(`Failed to fetch coaching queue: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Coaching insights response from API
 */
export interface OverviewInsightsResponse {
  insights: { title: string; detail: string }[];
}

/**
 * Fetch coaching insights for the overview dashboard
 *
 * @param params - Filter parameters (date range, threshold)
 * @param token - JWT access token
 * @returns Coaching insights list
 */
export async function fetchOverviewInsights(
  params: {
    dateFrom?: Date;
    dateTo?: Date;
    threshold?: number;
  },
  token?: string | null
): Promise<OverviewInsightsResponse> {
  const queryParams = new URLSearchParams();

  if (params.dateFrom) {
    queryParams.set('date_from', params.dateFrom.toISOString());
  }

  if (params.dateTo) {
    queryParams.set('date_to', params.dateTo.toISOString());
  }

  if (params.threshold !== undefined) {
    queryParams.set('threshold', params.threshold.toString());
  }

  const path = `/overview/insights${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);

  if (!response.ok) {
    throw new Error(`Failed to fetch overview insights: ${response.statusText}`);
  }

  return response.json();
}

// ==================== REP LEADERBOARD ====================

/**
 * Rep leaderboard item from API
 */
export interface RepLeaderboardItem {
  rank: number;
  rep: string;
  conversation_count: number;
  avg_composite: number;
  strongest: string;
  strongest_score: number;
  weakest: string;
  weakest_score: number;
  trend: number;
}

/**
 * Rep leaderboard response from API
 */
export interface RepLeaderboardResponse {
  items: RepLeaderboardItem[];
}

/**
 * Fetch representative leaderboard for the overview dashboard
 *
 * @param params - Filter parameters (date range, limit, includeTrend)
 * @param token - JWT access token
 * @returns Rep leaderboard data
 */
export async function fetchRepLeaderboard(
  params: {
    dateFrom?: Date;
    dateTo?: Date;
    limit?: number;
    includeTrend?: boolean;
  },
  token?: string | null
): Promise<RepLeaderboardResponse> {
  const queryParams = new URLSearchParams();

  if (params.dateFrom) {
    queryParams.set('date_from', params.dateFrom.toISOString());
  }

  if (params.dateTo) {
    queryParams.set('date_to', params.dateTo.toISOString());
  }

  if (params.limit !== undefined) {
    queryParams.set('limit', params.limit.toString());
  }

  if (params.includeTrend !== undefined) {
    queryParams.set('include_trend', params.includeTrend.toString());
  }

  const path = `/overview/rep-leaderboard${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiFetch(path, {}, token);

  if (!response.ok) {
    throw new Error(`Failed to fetch rep leaderboard: ${response.statusText}`);
  }

  return response.json();
}

// ==================== MODEL HEALTH ====================

/**
 * Model health response from API
 */
export interface ModelHealthResponse {
  model_name: string;
  prompt_version: string;
  last_eval_date: string;  // ISO datetime
  macro_pearson_r: number;
  macro_qwk: number;
  avg_latency_ms: number | null;  // null if no latency data available
  status: "healthy" | "warning" | "critical";
}

/**
 * Fetch model health/calibration data for the overview dashboard
 *
 * @param token - JWT access token
 * @returns Model health data, or null if no evaluation exists
 */
export async function fetchModelHealth(
  token?: string | null
): Promise<ModelHealthResponse | null> {
  const response = await apiFetch('/overview/model-health', {}, token);

  if (!response.ok) {
    throw new Error(`Failed to fetch model health: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Transform API response from snake_case to camelCase
 *
 * @param data - Raw API response with snake_case keys
 * @returns Transformed data matching ModelHealthData interface
 */
export function transformModelHealth(data: ModelHealthResponse): ModelHealthData {
  return {
    modelName: data.model_name,
    promptVersion: data.prompt_version,
    lastEvalDate: data.last_eval_date,
    macroPearsonR: data.macro_pearson_r,
    macroQWK: data.macro_qwk,
    avgLatencyMs: data.avg_latency_ms ?? undefined,  // Convert null to undefined for optional field
    status: data.status
  };
}

// ============================================================================
// Seed Management API
// ============================================================================

/**
 * Fetch current seeding status and data counts.
 *
 * Public endpoint - no authentication required.
 *
 * @returns Seed status with organization breakdown and totals
 */
export async function fetchSeedStatus(): Promise<SeedStatusResponse> {
  const response = await apiFetch('/seed/status', {}, null);
  if (!response.ok) {
    throw new Error(`Failed to fetch seed status: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Trigger manual seeding operation.
 *
 * WARNING: This deletes ALL existing data in the database
 * (all organizations, users, representatives, transcripts, assessments)
 * before creating fresh demo data.
 *
 * Public endpoint - no authentication required.
 *
 * @returns Seed trigger response with deletion and creation summary
 */
export async function triggerSeed(): Promise<SeedTriggerResponse> {
  const response = await apiFetch('/seed/trigger', { method: 'POST' }, null);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to trigger seed: ${errorText}`);
  }
  return response.json();
}
