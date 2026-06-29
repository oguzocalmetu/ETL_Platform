// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Connection ────────────────────────────────────────────────────────────────
export type ConnectionType = 'POSTGRESQL' | 'MYSQL' | 'MSSQL' | 'CSV' | 'EXCEL' | 'SFTP';

export interface Connection {
  id: string;
  name: string;
  type: ConnectionType;
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  extra_config: Record<string, unknown>;
  is_active: boolean;
  last_tested_at?: string;
  last_test_status?: 'SUCCESS' | 'FAILED';
  last_test_error?: string;
  created_at: string;
  updated_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  latency_ms?: number;
  error?: string;
  server_version?: string;
}

// ── Schema ────────────────────────────────────────────────────────────────────
export interface SchemaColumn {
  name: string;
  data_type: string;
  is_nullable: boolean;
  precision?: number;
  scale?: number;
  max_length?: number;
}

// ── Pipeline ──────────────────────────────────────────────────────────────────
export type LoadStrategy = 'APPEND' | 'FULL_LOAD' | 'TRUNCATE_INSERT' | 'UPSERT' | 'INCREMENTAL' | 'OVERWRITE';
export type PipelineStatus = 'DRAFT' | 'ACTIVE' | 'DISABLED';

export interface TransformRule {
  id?: string;
  transform_type: string;
  params: Record<string, unknown>;
  apply_order: number;
}

export interface ColumnMapping {
  id?: string;
  source_column?: string;
  target_column: string;
  source_type?: string;
  target_type?: string;
  is_constant: boolean;
  constant_value?: string;
  default_value?: string;
  is_nullable: boolean;
  is_excluded: boolean;
  ordinal_position: number;
  transform_rules: TransformRule[];
}

export interface ValidationRule {
  id?: string;
  mapping_id?: string;
  rule_type: string;
  params: Record<string, unknown>;
  action_on_fail: 'REJECT' | 'WARN' | 'STOP';
}

export interface Schedule {
  cron_expr?: string;
  interval_secs?: number;
  is_active: boolean;
}

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  source_connection_id?: string;
  target_connection_id?: string;
  source_config: Record<string, unknown>;
  target_config: Record<string, unknown>;
  load_strategy: LoadStrategy;
  upsert_keys?: string[];
  status: PipelineStatus;
  batch_size: number;
  created_at: string;
  updated_at: string;
  // Detail fields
  column_mappings?: ColumnMapping[];
  validation_rules?: ValidationRule[];
  schedule?: Schedule;
}

// ── Jobs ──────────────────────────────────────────────────────────────────────
export type JobStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
export type RunType = 'MANUAL' | 'SCHEDULED' | 'TEST';

export interface JobRun {
  id: string;
  pipeline_id: string;
  celery_task_id?: string;
  status: JobStatus;
  run_type: RunType;
  started_at?: string;
  finished_at?: string;
  duration_seconds?: number;
  source_count?: number;
  target_count?: number;
  success_count?: number;
  error_count?: number;
  rejected_count?: number;
  error_message?: string;
  created_at: string;
}

export interface JobRunLog {
  id: number;
  level: 'INFO' | 'WARN' | 'ERROR';
  stage?: string;
  message: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface RejectedRecord {
  id: number;
  row_number?: number;
  source_data: Record<string, unknown>;
  error_column?: string;
  error_rule?: string;
  error_message?: string;
  created_at: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_pipelines: number;
  active_pipelines: number;
  today_success_jobs: number;
  today_failed_jobs: number;
  today_rows_transferred: number;
  avg_duration_seconds: number;
}
