import React from 'react';
import { Form, Select, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { connectionsApi } from '../../../api/connections';
import type { WizardState } from './PipelineWizard';
const { Title, Text } = Typography;
export const Step4TargetConnection: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const { data: connections = [] } = useQuery({ queryKey: ['connections'], queryFn: () => connectionsApi.list() });
  return (
    <div>
      <Title level={4}>Hedef Bağlantı</Title>
      <Text type="secondary">Verinin yazılacağı hedef sistemin bağlantısını seçin.</Text>
      <Form layout="vertical" style={{ marginTop: 24, maxWidth: 480 }}>
        <Form.Item label="Hedef Bağlantı" required>
          <Select value={state.target_connection_id || undefined} onChange={(v) => onChange({ target_connection_id: v })} placeholder="Hedef bağlantı seçin" showSearch>
            {connections.map((c: any) => <Select.Option key={c.id} value={c.id}>{c.name} ({c.type})</Select.Option>)}
          </Select>
        </Form.Item>
      </Form>
    </div>
  );
};
