import React from 'react';
import { Button, Descriptions, Space, Typography, Divider, Alert } from 'antd';
import type { WizardState } from './PipelineWizard';
const { Title } = Typography;
export const Step11Review: React.FC<{ state: WizardState; onPublish: () => void; loading: boolean }> = ({ state, onPublish, loading }) => (
  <div>
    <Title level={4}>Özet ve Yayınlama</Title>
    <Alert type="info" message="Pipeline yayınlandıktan sonra çalıştırılabilir hale gelir." showIcon style={{ marginBottom: 16 }} />
    <Descriptions bordered size="small" column={1}>
      <Descriptions.Item label="Pipeline Adı">{state.name || '—'}</Descriptions.Item>
      <Descriptions.Item label="Kaynak Connection ID">{state.source_connection_id || '—'}</Descriptions.Item>
      <Descriptions.Item label="Kaynak Tablo">{state.source_table || state.source_query || '—'}</Descriptions.Item>
      <Descriptions.Item label="Hedef Connection ID">{state.target_connection_id || '—'}</Descriptions.Item>
      <Descriptions.Item label="Hedef Tablo">{state.target_table || '—'}</Descriptions.Item>
      <Descriptions.Item label="Load Strategy">{state.load_strategy}</Descriptions.Item>
      <Descriptions.Item label="Batch Boyutu">{state.batch_size?.toLocaleString()}</Descriptions.Item>
      <Descriptions.Item label="Kolon Eşleştirme">{state.column_mappings.length} eşleştirme</Descriptions.Item>
    </Descriptions>
    <Divider />
    <Button type="primary" size="large" loading={loading} onClick={onPublish} disabled={!state.name || !state.source_connection_id || !state.target_connection_id}>
      Pipeline'ı Yayınla
    </Button>
  </div>
);
