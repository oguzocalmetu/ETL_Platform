import React from 'react';
import { Button, Card, Table, Space, Typography, Tag, Popconfirm, message } from 'antd';
import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { pipelinesApi } from '../../api/pipelines';
import { jobsApi } from '../../api/jobs';
import { PipelineStatusBadge } from '../../components/common/StatusBadge';
import type { Pipeline } from '../../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const STRATEGY_COLOR: Record<string, string> = {
  APPEND: 'blue', FULL_LOAD: 'cyan', INCREMENTAL: 'green',
  UPSERT: 'orange', TRUNCATE_INSERT: 'red', OVERWRITE: 'volcano',
};

export const PipelinesPage: React.FC = () => {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [msgApi, contextHolder] = message.useMessage();

  const { data: pipelines = [], isLoading } = useQuery({
    queryKey: ['pipelines'],
    queryFn: () => pipelinesApi.list(),
  });

  const runMutation = useMutation({
    mutationFn: (pipelineId: string) => jobsApi.run(pipelineId, 'MANUAL'),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ['jobs'] });
      msgApi.success(`Job başlatıldı: ${job.id.slice(0, 8)}…`);
      navigate('/jobs');
    },
    onError: (e: any) => msgApi.error(e.response?.data?.detail || 'Job başlatılamadı'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => pipelinesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pipelines'] }); msgApi.success('Pipeline devre dışı bırakıldı'); },
  });

  const columns = [
    {
      title: 'Ad', dataIndex: 'name', key: 'name',
      render: (n: string, r: Pipeline) => (
        <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/pipelines/${r.id}`)}>
          <strong>{n}</strong>
        </Button>
      ),
    },
    { title: 'Durum', dataIndex: 'status', key: 'status', render: (s: any) => <PipelineStatusBadge status={s} /> },
    {
      title: 'Strateji', dataIndex: 'load_strategy', key: 'strategy',
      render: (s: string) => <Tag color={STRATEGY_COLOR[s] || 'default'}>{s}</Tag>,
    },
    { title: 'Batch', dataIndex: 'batch_size', key: 'batch', render: (n: number) => n?.toLocaleString() },
    {
      title: 'Son Güncelleme', dataIndex: 'updated_at', key: 'updated_at',
      render: (t: string) => dayjs(t).format('DD/MM/YY HH:mm'),
    },
    {
      title: 'İşlem', key: 'actions',
      render: (_: any, r: Pipeline) => (
        <Space>
          <Button
            type="primary" icon={<PlayCircleOutlined />} size="small"
            disabled={r.status !== 'ACTIVE'}
            loading={runMutation.isPending}
            onClick={() => runMutation.mutate(r.id)}
          >Çalıştır</Button>
          <Button icon={<EditOutlined />} size="small" onClick={() => navigate(`/pipelines/${r.id}/edit`)}>Düzenle</Button>
          <Popconfirm title="Bu pipeline'ı devre dışı bırakmak istediğinize emin misiniz?" onConfirm={() => deleteMutation.mutate(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {contextHolder}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Pipelines</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/pipelines/new')}>
          Yeni Pipeline
        </Button>
      </div>

      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Table dataSource={pipelines} columns={columns} rowKey="id" loading={isLoading} />
      </Card>
    </div>
  );
};
