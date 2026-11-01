/**
 * TypeScript boundary interfaces for Hydra API contracts.
 */

export interface SubjectScoreDto {
  subject_code: string;
  subject_name: string;
  score: number;
  max_score?: number;
  grading_scale?: string;
}

export interface StudentProfileRequest {
  student_id?: string;
  subject_scores: SubjectScoreDto[];
  entrance_exam_name?: string;
  entrance_rank?: number;
  preferred_locations?: string[];
  total_budget_inr: number;
  preferred_disciplines?: string[];
  career_goals?: string[];
  certifications?: string[];
}

export interface AcademicPrerequisiteDto {
  subject_code: string;
  subject_name: string;
  min_score: number;
  grading_scale: string;
  is_mandatory: boolean;
}

export interface EntrancePrerequisiteDto {
  exam_name: string;
  max_rank?: number;
  is_mandatory: boolean;
}

export interface ProgrammeResponse {
  programme_id: string;
  title: string;
  institution_name: string;
  location: string;
  discipline: string;
  annual_tuition_inr: number;
  duration_years: number;
  estimated_total_tuition_inr: number;
  currency: string;
  cost_basis: string;
  academic_prerequisites: AcademicPrerequisiteDto[];
  entrance_prerequisites: EntrancePrerequisiteDto[];
  skills_developed: string[];
  career_paths: string[];
  is_synthetic: boolean;
  dataset_label: string;
  provenance: string;
}

export interface RuleOutcomeDto {
  rule_id: string;
  rule_name: string;
  status: 'SATISFIED' | 'VIOLATED' | 'NEEDS_REVIEW' | string;
  facts_used: Record<string, unknown>;
  expected_value: string;
  observed_value: string;
  explanation: string;
  is_mandatory: boolean;
}

export interface AffordabilityDto {
  is_affordable: boolean;
  total_budget_inr: number;
  estimated_total_tuition_inr: number;
  currency: string;
  cost_basis: string;
}

export interface PreferenceFitDto {
  fit_score: number;
  criteria_breakdown: Record<string, number>;
  notes: string;
}

export interface DataProvenanceDto {
  is_synthetic: boolean;
  dataset_label: string;
  provenance: string;
}

export interface DiscoveredRelationshipDto {
  source: string;
  relationship: string;
  target: string;
  target_type: string;
  source_type?: 'direct' | 'inherited' | 'traversed' | string;
  provenance_path?: string[];
}

export interface ReasoningTreeNodeDto {
  node_id: string;
  expression_type: string;
  status: 'SATISFIED' | 'VIOLATED' | 'NEEDS_REVIEW' | string;
  is_mandatory: boolean;
  expected_value: string;
  observed_value: string;
  facts_used?: Record<string, unknown>;
  evidence?: string[];
  missing_facts?: string[];
  explanation: string;
  provenance?: string | null;
  children?: ReasoningTreeNodeDto[];
}

export interface ProgrammeEvaluationDto {
  programme_id: string;
  programme_title: string;
  institution_name: string;
  location: string;
  discipline: string;
  eligibility_status: 'eligible' | 'ineligible' | 'needs_review';
  affordability: AffordabilityDto;
  preference_fit: PreferenceFitDto;
  evidence: string[];
  rules_fired: RuleOutcomeDto[];
  reasoning_trace: string;
  missing_facts: string[];
  data_provenance: DataProvenanceDto;
  discovered_relationships: DiscoveredRelationshipDto[];
  reasoning_tree?: ReasoningTreeNodeDto | null;
  parent_frame_id?: string | null;
}

export interface EvaluationResponse {
  evaluations: ProgrammeEvaluationDto[];
  discovered_relationships: DiscoveredRelationshipDto[];
  is_synthetic: boolean;
  audit_timestamp: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface SourceDocumentDto {
  source_id: string;
  title: string;
  issuing_authority: string;
  canonical_url: string;
  source_type: string;
  academic_year: number;
  retrieval_timestamp: string;
  source_status: 'official_source' | 'derived_from_official' | 'synthetic_demo' | 'unverified' | string;
  publication_date?: string | null;
  original_artifact_path?: string | null;
  sha256_checksum?: string | null;
  document_version?: string | null;
  access_notes: string;
  verification_notes: string;
}

export interface DatasetSnapshotDto {
  snapshot_id: string;
  dataset_id: string;
  snapshot_version: string;
  academic_year: number;
  source_document_ids: string[];
  importer_version: string;
  source_artifact_checksum: string;
  created_at: string;
  records_processed: number;
  records_accepted: number;
  records_quarantined: number;
  records_duplicate: number;
  validation_status: 'valid' | 'quarantined' | 'pending' | string;
  quarantine_file_path?: string | null;
}

export interface AdmissionCutoffDto {
  observation_id: string;
  institution_id: string;
  programme_id: string;
  institution_name: string;
  programme_title: string;
  academic_year: number;
  counselling_round: number;
  exam_name: string;
  quota: string;
  seat_type: string;
  gender_pool: string;
  opening_rank: number;
  closing_rank: number;
  rank_basis: string;
  source_document_id: string;
  snapshot_id: string;
  source_row_provenance: string;
  validation_status: string;
  source_status: string;
  is_synthetic: boolean;
  disclaimer: string;
}

export interface AdmissionsProgrammeDto {
  programme_id: string;
  institution_id: string;
  official_title: string;
  academic_year: number;
  degree_type?: string | null;
  discipline?: string | null;
  duration_years?: number | null;
  source_references: string[];
  provenance: string;
  is_synthetic: boolean;
}

export interface FormalEligibilityCriterionDto {
  criterion_id: string;
  authority: string;
  academic_year: number;
  criterion_number: string;
  title: string;
  description: string;
  source_document_id: string;
  source_status: string;
  is_mandatory: boolean;
  criterion_scope?: string;
  target_examination?: string | null;
}

export interface PaginatedCutoffsResponse {
  total_count: number;
  limit: number;
  offset: number;
  results: AdmissionCutoffDto[];
  disclaimer: string;
}

export interface PaginatedProgrammesResponse {
  total_count: number;
  limit: number;
  offset: number;
  results: AdmissionsProgrammeDto[];
}

export interface FactRecordDto {
  fact_id: string;
  field_name: string;
  actual_value: unknown;
  original_value: unknown;
  unit_or_scale?: string | null;
  origin_category: 'user_provided' | 'deterministically_derived' | 'external_verified' | 'unknown' | string;
  validation_status: 'valid' | 'needs_review' | 'invalid' | 'missing' | string;
  explanation: string;
  evidence_reference?: string | null;
  input_fact_ids?: string[];
  derivation_rule?: string | null;
}

export interface NormalizedSubjectScoreDto {
  subject_code: string;
  subject_name: string;
  original_score: number;
  max_score: number;
  grading_scale: string;
  normalized_percentage?: number | null;
  conversion_status: 'valid' | 'needs_review' | 'invalid' | string;
  conversion_explanation: string;
}

export interface AcademicIdentityDto {
  subject_scores: NormalizedSubjectScoreDto[];
  academic_strengths: string[];
  missing_subjects: string[];
  unsupported_grading_scales: string[];
}

export interface EntranceExamProfileDto {
  exam_name?: string | null;
  rank?: number | null;
  rank_basis?: string | null;
  academic_year?: number | null;
  missing_details: string[];
  interpretation_notes: string;
}

export interface FinancialConstraintsDto {
  total_budget_inr: number;
  currency: string;
  cost_basis: string;
  is_budget_provided: boolean;
  affordability_readiness: boolean;
  notes: string;
}

export interface GeographicPreferencesDto {
  preferred_locations: string[];
  is_unconstrained: boolean;
  notes: string;
}

export interface InterestsAndGoalsDto {
  preferred_disciplines: string[];
  career_goals: string[];
  certifications: string[];
  unmapped_interests: string[];
}

export interface DimensionCompletenessDto {
  dimension_name: string;
  state: 'complete' | 'partial' | 'needs_review' | string;
  available_facts: string[];
  missing_facts: string[];
  invalid_facts: string[];
  review_facts: string[];
  explanation: string;
}

export interface TwinSnapshotDto {
  twin_id: string;
  student_id?: string | null;
  student_profile_version: string;
  schema_version: string;
  created_at: string;
  profile_fingerprint: string;
  overall_completeness: 'complete' | 'partial' | 'needs_review' | string;
  completeness_dimensions: Record<string, DimensionCompletenessDto>;
  academic_identity: AcademicIdentityDto;
  entrance_exam_profile: EntranceExamProfileDto;
  financial_constraints: FinancialConstraintsDto;
  geographic_preferences: GeographicPreferencesDto;
  interests_and_goals: InterestsAndGoalsDto;
  facts: Record<string, FactRecordDto>;
  semantic_network_pathways: DiscoveredRelationshipDto[];
  frame_representation: Record<string, unknown>;
  missing_information: string[];
  validation_findings: string[];
  is_synthetic: boolean;
}

export interface StudentTwinResponse {
  snapshot: TwinSnapshotDto;
  disclaimer: string;
}



