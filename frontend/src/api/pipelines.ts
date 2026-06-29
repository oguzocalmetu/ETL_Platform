import apiClient from './client';
import type { Pipeline, ColumnMapping, ValidationRule } from '../types';

export const pipelinesApi = {
  list: (params?: { status?: string }) =>
    apiClient.get<Pipeline[]>('/pipelines', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Pipeline>(`/pipelines/${id}`).then((r) => r.data),

  create: (data: Partial<Pipeline>) =>
    apiClient.post<Pipeline>('/pipelines', data).then((r) => r.data),

  update: (id: string, data: Partial<Pipeline>) =>
    apiClient.put<Pipeline>(`/pipelines/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/pipelines/${id}`),

  publish: (id: string) =>
    apiClient.post<Pipeline>(`/pipelines/${id}/publish`).then((r) => r.data),

  saveMappings: (id: string, mappings: ColumnMapping[]) =>
    apiClient.put(`/pipelines/${id}/mappings`, mappings).then((r) => r.data),

  saveValidations: (id: string, rules: ValidationRule[]) =>
    apiClient.put(`/pipelines/${id}/validations`, rules).then((r) => r.data),
};
