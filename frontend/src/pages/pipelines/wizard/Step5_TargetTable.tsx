import React from 'react';
import { Form, Select, Input, Switch, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { schemaApi } from '../../../api/connections';
import type { WizardState } from './PipelineWizard';
const { Title, Text } = Typography;
export const Step5TargetTable: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const { data: tables = [], isLoading } = useQuery({
    queryKey: ['target-tables', state.target_connection_id],
    queryFn: () => schemaApi.listTables(state.target_connection_id),
    enabled: !!state.target_connection_id,
  });
  return (
    <div>
      <Title level={4}>Hedef Tablo</Title>
      <Form layout="vertical" style={{ maxWidth: 480, marginTop: 16 }}>
        <Form.Item label="Hedef Tablo" required>
          <Select value={state.target_table || undefined} onChange={(v) => onChange({ target_table: v })}
            loading={isLoading} placeholder="Hedef tablo seçin" showSearch>
            {tables.map((t: string) => <Select.Option key={t} value={t}>{t}</Select.Option>)}
          </Select>
        </Form.Item>
        <Text type="secondary" style={{ fontSize: 12 }}>Tablo listede yoksa yukarıya tablo adını yazabilirsiniz.</Text>
      </Form>
    </div>
  );
};
