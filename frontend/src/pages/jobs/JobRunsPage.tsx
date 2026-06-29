import React, { useState } from 'react';
import { Card, Table, Typography, Button, Space, Drawer, Timeline, Tag, Alert, Spin } from 'antd';
import { ReloadOutlined, EyeOutlined, StopOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi } from '../../api/jobs';
import { JobStatusBadge } from '../../components/common/StatusBadge';
import type { JobRun, JobRunLog } from '../../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const LOG_ICON: Record<string, string> = { INFO: '✅', WARN: '⚠️', ERROR: '❌' };

export const JobRunsPage: React.FC = () => {
  const [selectedJob, setSelectedJob] = useState<JobRun | null>(null);
  const [logsOpen, setLogsOpen] = useState(false);
  const qc = useQueryClient();

  const { data: jobs = [], isLoading, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list({ limit: 50 }),
    refetchInterval: 10_000,
  });

  const { data: logs = [], isLoading: logsLoading } = useQuery({
    queryKey: ['job-logs', selectedJob?.id],
    queryFn: () => jobsApi.getLogs(selectedJob!.id),
    enabled: !!selectedJob && logsOpen,
    refetchInterval: selectedJob?.status === 'RUNNING' ? 2000 : false,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => jobsApi.cancel(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['jobs'] }); },
  });

  const openLogs = (job: JobRun) => { setSelectedJob(job); setLogsOpen(true); };

  const columns = [
    {
      title: 'Pipeline', dataIndex: 'pipeline_id', key: 'pipeline',
      render: (id: string) => <Text code style={{ fontSize: 11 }}>{id.slice(0, 8)}…</Text>,
    },
    { title: 'Durum', dataIndex: 'status', key: 'status', render: (s: any) => <JobStatusBadge status={s} /> },
    { title: 'Tür', dataIndex: 'run_type', key: 'type', render: (t: string) => <Tag>{t}</Tag> },
    {
      title: 'Başlangıç', dataIndex: 'started_at', key: 'started_at',
      render: (t: string) => t ? dayjs(t).format('DD/MM/YY HH:mm:ss') : '—',
    },
    {
      title: 'Süre', dataIndex: 'duration_seconds', key: 'duration',
      render: (d: number) => d != null ? `${d.toFixed(1)}s` : '—',
    },
    {
      title: 'Kaynak', dataIndex: 'source_count', key: 'source',
      render: (n: number) => n?.toLocaleString() ?? '—',
    },
    {
      title: 'Başarılı', dataIndex: 'success_count', key: 'success',
      render: (n: number) => n != null ? <Text style={{ color: '#52c41a' }}>{n.toLocaleString()}</Text> : '—',
    },
    {
      title: 'Reddedilen', dataIndex: 'rejected_count', key: 'rejected',
      render: (n: number) => n ? <Text style={{ color: '#faad14' }}>{n.toLocaleString()}</Text> : '—',
    },
    {
      title: 'İşlem', key: 'actions',
      render: (_: any, r: JobRun) => (
        <Space>
          <Button icon={<EyeOutlined />} size="small" onClick={() => openLogs(r)}>Loglar</Button>
          {['PENDING', 'RUNNING'].includes(r.status) && (
            <Button icon={<StopOutlined />} size="small" danger
              loading={cancelMutation.isPending}
              onClick={() => cancelMutation.mutate(r.id)}>İptal</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Job Runs</Title>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Yenile</Button>
      </div>

      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Table dataSource={jobs} columns={columns} rowKey="id" loading={isLoading} size="small"
          rowClassName={(r) => r.status === 'FAILED' ? 'ant-table-row-error' : ''} />
      </Card>

      {/* Log Drawer */}
      <Drawer
        title={
          <Space>
            <span>Job Logs</span>
            {selectedJob && <JobStatusBadge status={selectedJob.status} />}
          </Space>
        }
        open={logsOpen}
        onClose={() => setLogsOpen(false)}
        width={640}
      >
        {selectedJob?.error_message && (
          <Alert type="error" message={selectedJob.error_message} showIcon style={{ marginBottom: 16 }} />
        )}

        {logsLoading ? (
          <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>
        ) : (
          <Timeline
            items={logs.map((log: JobRunLog) => ({
              color: log.level === 'ERROR' ? 'red' : log.level === 'WARN' ? 'orange' : 'green',
              children: (
                <div>
                  <Space>
                    <Text style={{ fontSize: 12 }}>{LOG_ICON[log.level]}</Text>
                    <Tag style={{ fontSize: 10 }}>{log.stage || 'GENERAL'}</Tag>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {dayjs(log.created_at).format('HH:mm:ss.SSS')}
                    </Text>
                  </Space>
                  <div><Text style={{ fontSize: 13 }}>{log.message}</Text></div>
                </div>
              ),
            }))}
          />
        )}
      </Drawer>
    </div>
  );
};
