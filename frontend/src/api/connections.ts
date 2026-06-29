import apiClient from './client';
import type { Connection, ConnectionTestResult } from '../types';

export const connectionsApi = {
  list: (params?: { type?: string; is_active?: boolean }) =>
    apiClient.get<Connection[]>('/connections', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Connection>(`/connections/${id}`).then((r) => r.data),

  create: (data: Partial<Connection> & { password?: string }) =>
    apiClient.post<Connection>('/connections', data).then((r) => r.data),

  update: (id: string, data: Partial<Connection> & { password?: string }) =>
    apiClient.put<Connection>(`/connections/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/connections/${id}`),

  test: (id: string) =>
    apiClient.post<ConnectionTestResult>(`/connections/${id}/test`).then((r) => r.data),
};

export const schemaApi = {
  listTables: (connectionId: string) =>
    apiClient.get<{ tables: string[] }>(`/schema/${connectionId}/tables`).then((r) => r.data.tables),

  getColumns: (connectionId: string, table: string) =>
    apiClient.get(`/schema/${connectionId}/columns`, { params: { table } }).then((r) => r.data),

  preview: (connectionId: string, table: string, limit = 20) =>
    apiClient.post(`/schema/${connectionId}/preview`, null, { params: { table, limit } }).then((r) => r.data),
};
