import React from 'react';
import { Form, Select, Card, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { connectionsApi } from '../../../api/connections';
import type { WizardState } from './PipelineWizard';

const { Title, Text } = Typography;

export const Step2SourceConnection: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const { data: connections = [] } = useQuery({ queryKey: ['connections'], queryFn: () => connectionsApi.list() });
  return (
    <div>
      <Title level={4}>Kaynak Bağlantı</Title>
      <Text type="secondary">Verinin okunacağı kaynak sistemin bağlantısını seçin.</Text>
      <Form layout="vertical" style={{ marginTop: 24, maxWidth: 480 }}>
        <Form.Item label="Kaynak Bağlantı" required>
          <Select value={state.source_connection_id || undefined} onChange={(v) => onChange({ source_connection_id: v })} placeholder="Bağlantı seçin" showSearch>
            {connections.map((c: any) => <Select.Option key={c.id} value={c.id}>{c.name} ({c.type})</Select.Option>)}
          </Select>
        </Form.Item>
      </Form>
    </div>
  );
};
