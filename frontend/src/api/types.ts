/**
 * TypeScript boundary interfaces for Hydra API contracts.
 */

export interface SubjectScoreDto {
  subject_code: string;
  subject_name: string;
  score: number;
  max_score?: number;
  grading_scale?: string;
  board?: string | null;
  conversion_policy_id?: string | null;
  examination_year?: number | null;
  is_indicative?: boolean;
  is_institution_authorized?: boolean;
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
  board?: string | null;
  conversion_policy_id?: string | null;
  examination_year?: number | null;
  is_indicative?: boolean;
  is_institution_authorized?: boolean;
}

export interface AcademicIdentityDto {
  subject_scores: NormalizedSubjectScoreDto[];
  score_based_academic_highlights: string[];
  academic_strengths: string[];
  highlight_threshold: number;
  highlight_heuristic_version: string;
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
  preference_type: 'not_provided' | 'preferred_locations' | 'anywhere_in_india' | string;
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
  snapshot_id?: string;
  student_id?: string | null;
  student_profile_version: string;
  schema_version: string;
  policy_version?: string;
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

export interface ScoringPolicyDto {
  policy_version: string;
  weight_discipline: number;
  weight_career: number;
  weight_academic: number;
  weight_geographic: number;
}

export interface AuctionRequestDto {
  snapshot_id?: string;
  twin_id?: string;
  profile?: StudentProfileRequest;
  programme_ids?: string[];
  scoring_policy?: ScoringPolicyDto;
}

export interface ProgrammeBidDto {
  bid_id: string;
  agent_id: string;
  programme_id: string;
  programme_title: string;
  institution_name: string;
  twin_id: string;
  snapshot_id: string;
  eligibility_status: 'eligible' | 'ineligible' | 'needs_review' | string;
  affordability_status: boolean;
  total_budget_inr: number;
  estimated_total_tuition_inr: number;
  currency: string;
  cost_basis: string;
  academic_alignment: number;
  discipline_alignment: number;
  career_alignment: number;
  geographic_alignment: number;
  composite_preference_score: number | null;
  evidence_coverage_ratio?: number;
  active_dimensions?: string[];
  is_insufficient_evidence?: boolean;
  evidence_tier?: 'comprehensive' | 'partial' | 'exploratory' | 'unscored' | string;
  is_unscored?: boolean;
  neutral_baseline_display?: number;
  proposal_status: 'unconditional_candidate' | 'conditional_candidate' | 'no_bid' | string;
  policy_version: string;
  evidence_references: string[];
  missing_facts: string[];
  warnings: string[];
  reasoning_trace: Record<string, unknown>;
  created_at: string;
  is_synthetic: boolean;
  dataset_label: string;
}

export interface AuctionRankingItemDto {
  rank: number;
  bid: ProgrammeBidDto;
  explanation: string;
  tie_breaker_applied?: string | null;
}

export interface AuctionResultDto {
  auction_id: string;
  twin_id: string;
  snapshot_id: string;
  policy_version: string;
  total_bids: number;
  unconditional_candidates: AuctionRankingItemDto[];
  conditional_candidates: AuctionRankingItemDto[];
  no_bid_candidates: AuctionRankingItemDto[];
  ranked_bids: AuctionRankingItemDto[];
  auction_summary: string;
  executed_at: string;
}

export interface FranchiseInfoDto {
  programme_id: string;
  title: string;
  institution_name: string;
  location: string;
  discipline: string;
  agent_id: string;
  is_synthetic: boolean;
  dataset_label: string;
}

export interface PlanningActionDto {
  action_id: string;
  title: string;
  description: string;
  category: 'information_gathering' | 'documentation' | 'preparation' | 'eligibility_pathway' | 'preference_change' | 'non_actionable' | string;
  preconditions: string[];
  satisfies_conditions: string[];
  cost: number;
  cost_unit: string;
  duration_days: number;
  evidence_requirement?: string | null;
  is_actionable: boolean;
}

export interface PlanningRequestDto {
  target_programme_id: string;
  snapshot_id?: string;
  twin_id?: string;
  profile?: StudentProfileRequest;
  use_heuristic?: boolean;
}

export interface PlanningResultDto {
  plan_id: string;
  twin_id: string;
  snapshot_id: string;
  target_programme_id: string;
  target_programme_title: string;
  initial_status: string;
  goal_reached: boolean;
  actions: PlanningActionDto[];
  total_cost: number;
  total_duration_days: number;
  nodes_expanded: number;
  heuristic_used: string;
  alternative_routes: Array<{
    pathway_name: string;
    required_conditions: string[];
    currently_satisfied: string[];
    readiness_ratio: number;
  }>;
  explanation: string;
  warnings: string[];
  executed_at: string;
}

export interface MonteCarloConfigDto {
  iterations?: number;
  seed?: number;
  budget_std_dev_pct?: number;
  rank_slip_std_dev_pct?: number;
  tuition_inflation_mean_pct?: number;
}

export interface SimulationRequestDto {
  target_programme_id: string;
  scenario_type?: string;
  snapshot_id?: string;
  twin_id?: string;
  profile?: StudentProfileRequest;
  parameters?: Record<string, unknown>;
  monte_carlo_config?: MonteCarloConfigDto;
}

export interface ScenarioDefinitionDto {
  scenario_id: string;
  scenario_type: string;
  base_snapshot_id: string;
  changed_variables: Record<string, unknown>;
  original_values: Record<string, unknown>;
  hypothetical_values: Record<string, unknown>;
  assumptions: string[];
  is_hypothetical: boolean;
  random_seed?: number | null;
}

export interface DistributionMetricDto {
  variable_name: string;
  mean: number;
  median: number;
  p10: number;
  p50: number;
  p90: number;
  min_val: number;
  max_val: number;
}

export interface SimulationResultDto {
  simulation_id: string;
  snapshot_id: string;
  target_programme_id: string;
  scenario: ScenarioDefinitionDto;
  baseline_eligible: boolean;
  baseline_affordable: boolean;
  scenario_eligible: boolean;
  scenario_affordable: boolean;
  eligibility_changed: boolean;
  affordability_changed: boolean;
  monte_carlo_metrics?: Record<string, DistributionMetricDto> | null;
  monte_carlo_outcome_frequencies?: Record<string, number> | null;
  delta_summary: string;
  warnings: string[];
  executed_at: string;
}

export interface BossFightRequestDto {
  target_programme_id: string;
  snapshot_id?: string;
  twin_id?: string;
  profile?: StudentProfileRequest;
}

export interface AttackOutcomeDto {
  attack_type: string;
  perturbation_description: string;
  baseline_status: string;
  perturbed_status: string;
  survived: boolean;
  failed_constraint?: string | null;
  explanation: string;
}

export interface BossFightReportDto {
  report_id: string;
  target_programme_id: string;
  target_programme_title: string;
  snapshot_id: string;
  overall_robustness: 'robust_under_tested_scenarios' | 'fragile' | 'fails_under_tested_scenarios' | 'insufficient_evidence' | string;
  total_attacks_tested: number;
  attacks_survived: number;
  attacks_failed: number;
  attack_outcomes: AttackOutcomeDto[];
  surviving_alternative_programmes: string[];
  fallback_recommendation: string;
  disclaimer: string;
  executed_at: string;
}

// ==========================================
// M005: Oracle Forecasting Types
// ==========================================

export interface ForecastTargetDto {
  institution_id: string;
  programme_id: string;
  future_academic_year: number;
  counselling_round: number;
  exam_name: string;
  seat_type: string;
  quota: string;
  gender_pool: string;
  rank_basis: string;
  target_type: string;
}

export interface EvaluationMetricsDto {
  mae: number;
  median_absolute_error: number;
  baseline_mae: number;
  baseline_median_absolute_error: number;
  interval_coverage: number;
  train_samples: number;
  test_samples: number;
  interval_coverage_p10_p90?: number;
  interval_coverage_p5_p95?: number;
  coverage_ci_p10_p90?: [number, number];
  coverage_ci_p5_p95?: [number, number];
  nominal_coverage_p10_p90?: number;
  nominal_coverage_p5_p95?: number;
}

export interface CutoffForecastDto {
  target: ForecastTargetDto;
  status: string;
  point_prediction?: number | null;
  interval_p10?: number | null;
  interval_p90?: number | null;
  interval_p5?: number | null;
  interval_p95?: number | null;
  prediction_standard_error?: number | null;
  uncertainty_band?: number | null;
  interval_type?: string;
  is_calibrated?: boolean;
  calibration_notes?: string;
  holdout_samples_count?: number | null;
  empirical_coverage_p10_p90?: number | null;
  empirical_coverage_p5_p95?: number | null;
  coverage_confidence_interval?: [number, number] | null;
  nominal_coverage_rate?: number;
  calibration_tolerance?: number;
  model_version: string;
  training_snapshot_id?: string | null;
  training_records_count: number;
  training_date?: string | null;
  features_used: string[];
  metrics?: EvaluationMetricsDto | null;
  is_estimate: boolean;
  confidence: number;
  warnings: string[];
  disclaimer: string;
}

export interface OracleModelInfoDto {
  model_id: string;
  model_type: string;
  features: string[];
  is_trained: boolean;
  status: string;
  description: string;
}

export interface DataReadinessReportDto {
  total_records_inspected: number;
  eligible_records_count: number;
  rejected_records_count: number;
  rejections_by_reason: Record<string, number>;
  eligible_academic_years: number[];
  verified_sources_used: string[];
  status: string;
  message: string;
}

export interface OracleStatusResponseDto {
  status: string;
  readiness_report: DataReadinessReportDto;
  active_model_version: string;
  is_trained: boolean;
  models_available: any[];
}

// ==========================================
// M006: Interest Decoder Types
// ==========================================

export interface CanonicalConceptDto {
  concept_id: string;
  name: string;
  concept_type: string;
  description: string;
  keywords: string[];
  related_node_ids: string[];
}

export interface CandidateConceptDto {
  concept: CanonicalConceptDto;
  similarity_score: number;
  explanation: string;
  related_graph_nodes: Array<{ node_id: string; name: string; type: string }>;
  alternative_interpretations: string[];
  uncertainty: number;
  status: string;
  model_version: string;
  provenance: string;
  is_neural?: boolean;
}

export interface InterestDecodingResponseDto {
  input_text: string;
  candidates: CandidateConceptDto[];
  top_concept?: CandidateConceptDto | null;
  taxonomy_version: string;
  model_version: string;
  model_status?: string;
  dimensions?: number;
  is_estimate: boolean;
  disclaimer: string;
}

export interface ConfirmedInterestResponseDto {
  concept_id: string;
  concept_name: string;
  concept_type: string;
  original_similarity: number;
  confirmed_at: string;
  status: string;
}

export interface InterestModelStatusDto {
  status: string;
  model_id: string;
  architecture: string;
  dimensions: number;
  parameter_count: string;
  is_neural: boolean;
  taxonomy_version: string;
  canonical_concepts_indexed: number;
  similarity_metric: string;
  license: string;
  hardware_requirements: string;
  runtime_device: string;
  provenance: string;
}

// ==========================================
// M007: Central Referee Types
// ==========================================

export interface ConflictRecordDto {
  conflict_id: string;
  agents_involved: string[];
  field_or_claim: string;
  claim_a: string;
  claim_b: string;
  resolution_strategy: string;
  resolved_value?: string | null;
  is_resolved: boolean;
  explanation: string;
}

export interface RefereeProgrammeDecisionDto {
  programme_id: string;
  programme_title: string;
  institution_name: string;
  eligibility_status: string;
  is_affordable: boolean;
  tuition_inr: number;
  student_budget_inr: number;
  preference_fit: number;
  preference_evidence_coverage?: number;
  active_preference_dimensions?: string[];
  is_insufficient_preference_evidence?: boolean;
  franchise_proposal_status?: string | null;
  auction_rank?: number | null;
  oracle_status: string;
  oracle_forecast?: Record<string, any> | null;
  heist_plan_discovered: boolean;
  heist_plan_actions: string[];
  boss_fight_robustness?: string | null;
  boss_fight_survived: number;
  boss_fight_total: number;
  rule_traces: any[];
  decision_summary: string;
}

export interface AgentResponseEnvelopeDto {
  agent_name: string;
  agent_version: string;
  schema_version: string;
  snapshot_id: string;
  twin_id: string;
  execution_status: string;
  result: Record<string, any>;
  evidence_references: string[];
  assumptions: string[];
  warnings: string[];
  unknown_facts: string[];
  explanation: string;
  timestamp: string;
  error?: string | null;
}

export interface RefereeEvaluateRequestDto {
  profile?: StudentProfileRequest | null;
  snapshot_id?: string | null;
  include_auction?: boolean;
  include_planning?: boolean;
  include_stress_test?: boolean;
  include_oracle?: boolean;
  interest_narrative?: string | null;
}

export interface RefereeEvaluationResponseDto {
  evaluation_id: string;
  snapshot_id: string;
  twin_id: string;
  student_name: string;
  programme_decisions: RefereeProgrammeDecisionDto[];
  top_recommended_programmes: string[];
  conflicts_detected: ConflictRecordDto[];
  interest_decoder_result?: Record<string, any> | null;
  agent_envelopes: AgentResponseEnvelopeDto[];
  hierarchy_rules_applied: string[];
  audit_timestamp: string;
  disclaimer: string;
}

export interface UserInteractionEventDto {
  event_id: string;
  event_type: string;
  timestamp: string;
  target_id?: string;
  domain?: string;
  metadata?: Record<string, any>;
}

export interface NeuralTrajectoryInsightsDto {
  career_readiness_score: number;
  domain_affinity_weights: Record<string, number>;
  learning_velocity_index: number;
  risk_assessment_index: number;
  projected_career_outcomes: string[];
  model_architecture: string;
  confidence: number;
  is_estimate: boolean;
  provenance: string;
  is_synthetic: boolean;
}

export interface ComprehensiveAssessmentReportDto {
  report_id: string;
  student_id: string;
  generated_at: string;
  executive_summary: string;
  voice_script: string;
  academic_standing: Record<string, any>;
  verified_eligibility_breakdown: Record<string, number>;
  top_recommended_pathways: Array<{
    programme_id: string;
    title: string;
    institution: string;
    eligibility_status: string;
    affordability: boolean;
    confidence: number;
    pathway_strategy: string;
  }>;
  neural_insights: NeuralTrajectoryInsightsDto;
  actionable_milestones: Array<{
    phase: string;
    title: string;
    status: string;
    target_timeline: string;
    details: string;
  }>;
  is_synthetic: boolean;
  dataset_label: string;
  provenance: string;
}
