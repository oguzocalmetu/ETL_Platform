import React from 'react';
import { Tag } from 'antd';
import type { JobStatus, PipelineStatus } from '../../types';

const JOB_STATUS_MAP: Record<JobStatus, { color: string; label: string }> = {
  PENDING:   { color: 'default',  label: 'Bekliyor'   },
  RUNNING:   { color: 'processing', label: 'Çalışıyor' },
  SUCCESS:   { color: 'success',  label: 'Başarılı'   },
  FAILED:    { color: 'error',    label: 'Hata'        },
  CANCELLED: { color: 'warning',  label: 'İptal'       },
};

const PIPELINE_STATUS_MAP: Record<PipelineStatus, { color: string; label: string }> = {
  DRAFT:    { color: 'default', label: 'Taslak'  },
  ACTIVE:   { color: 'success', label: 'Aktif'   },
  DISABLED: { color: 'error',   label: 'Pasif'   },
};

export const JobStatusBadge: React.FC<{ status: JobStatus }> = ({ status }) => {
  const map = JOB_STATUS_MAP[status] || { color: 'default', label: status };
  return <Tag color={map.color}>{map.label}</Tag>;
};

export const PipelineStatusBadge: React.FC<{ status: PipelineStatus }> = ({ status }) => {
  const map = PIPELINE_STATUS_MAP[status] || { color: 'default', label: status };
  return <Tag color={map.color}>{map.label}</Tag>;
};
