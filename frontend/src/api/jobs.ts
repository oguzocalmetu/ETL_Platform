import apiClient from './client';
import type { JobRun, JobRunLog, RejectedRecord, DashboardStats } from '../types';

export const jobsApi = {
  run: (pipelineId: string, runType = 'MANUAL', testLimit?: number) =>
    apiClient.post<JobRun>('/jobs/run', {
      pipeline_id: pipelineId,
      run_type: runType,
      test_limit: testLimit,
    }).then((r) => r.data),

  list: (params?: { pipeline_id?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get<JobRun[]>('/jobs', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<JobRun>(`/jobs/${id}`).then((r) => r.data),

  getStatus: (id: string) =>
    apiClient.get(`/jobs/${id}/status`).then((r) => r.data),

  getLogs: (id: string) =>
    apiClient.get<JobRunLog[]>(`/jobs/${id}/logs`).then((r) => r.data),

  getRejected: (id: string, limit = 100) =>
    apiClient.get<RejectedRecord[]>(`/jobs/${id}/rejected`, { params: { limit } }).then((r) => r.data),

  cancel: (id: string) =>
    apiClient.post(`/jobs/${id}/cancel`).then((r) => r.data),
};

export const dashboardApi = {
  getStats: () =>
    apiClient.get<DashboardStats>('/dashboard/stats').then((r) => r.data),

  getRecentJobs: (limit = 10) =>
    apiClient.get('/dashboard/recent-jobs', { params: { limit } }).then((r) => r.data),
};
