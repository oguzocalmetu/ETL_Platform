import React from 'react';
import { Card, Col, Row, Statistic, Table, Typography, Tag, Space, Skeleton } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ApartmentOutlined,
  RiseOutlined, ClockCircleOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../../api/jobs';
import { JobStatusBadge } from '../../components/common/StatusBadge';
import dayjs from 'dayjs';

const { Title } = Typography;

export const DashboardPage: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30_000,
  });

  const { data: recentJobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['recent-jobs'],
    queryFn: () => dashboardApi.getRecentJobs(10),
    refetchInterval: 15_000,
  });

  const statCards = [
    { title: 'Toplam Pipeline', value: stats?.total_pipelines, icon: <ApartmentOutlined />, color: '#1677ff' },
    { title: 'Aktif Pipeline', value: stats?.active_pipelines, icon: <DatabaseOutlined />, color: '#52c41a' },
    { title: 'Bugün Başarılı', value: stats?.today_success_jobs, icon: <CheckCircleOutlined />, color: '#52c41a' },
    { title: 'Bugün Hatalı', value: stats?.today_failed_jobs, icon: <CloseCircleOutlined />, color: '#ff4d4f' },
    { title: 'Aktarılan Satır (bugün)', value: stats?.today_rows_transferred?.toLocaleString(), icon: <RiseOutlined />, color: '#1677ff' },
    { title: 'Ort. Süre (sn)', value: stats?.avg_duration_seconds, icon: <ClockCircleOutlined />, color: '#faad14' },
  ];

  const jobColumns = [
    { title: 'Pipeline', dataIndex: 'pipeline_name', key: 'pipeline_name', ellipsis: true },
    { title: 'Durum', dataIndex: 'status', key: 'status', render: (s: any) => <JobStatusBadge status={s} /> },
    { title: 'Tür', dataIndex: 'run_type', key: 'run_type', render: (t: string) => <Tag>{t}</Tag> },
    {
      title: 'Başlangıç', dataIndex: 'started_at', key: 'started_at',
      render: (t: string) => t ? dayjs(t).format('HH:mm:ss') : '—',
    },
    {
      title: 'Süre', dataIndex: 'duration_seconds', key: 'duration',
      render: (d: number) => d ? `${d.toFixed(1)}s` : '—',
    },
    {
      title: 'Satır', dataIndex: 'success_count', key: 'rows',
      render: (n: number) => n?.toLocaleString() ?? '—',
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>Dashboard</Title>

      {/* Stat Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statCards.map((card) => (
          <Col xs={24} sm={12} lg={8} xl={4} key={card.title}>
            <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
              {statsLoading ? (
                <Skeleton active paragraph={{ rows: 1 }} />
              ) : (
                <Statistic
                  title={card.title}
                  value={card.value}
                  prefix={React.cloneElement(card.icon, { style: { color: card.color } })}
                  valueStyle={{ color: card.color }}
                />
              )}
            </Card>
          </Col>
        ))}
      </Row>

      {/* Recent Jobs */}
      <Card title="Son Job Çalışmaları" bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Table
          dataSource={recentJobs || []}
          columns={jobColumns}
          rowKey="id"
          loading={jobsLoading}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};
