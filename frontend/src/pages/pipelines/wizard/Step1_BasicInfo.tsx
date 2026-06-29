import React from 'react';
import { Form, Input, Typography } from 'antd';
import type { WizardState } from './PipelineWizard';

const { Title, Text } = Typography;

export const Step1BasicInfo: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => (
  <div>
    <Title level={4}>Pipeline Bilgileri</Title>
    <Text type="secondary">Pipeline'a açıklayıcı bir ad ve açıklama verin.</Text>
    <Form layout="vertical" style={{ marginTop: 24, maxWidth: 480 }}>
      <Form.Item label="Pipeline Adı" required>
        <Input value={state.name} onChange={(e) => onChange({ name: e.target.value })} placeholder="orders_to_dwh" />
      </Form.Item>
      <Form.Item label="Açıklama">
        <Input.TextArea value={state.description} onChange={(e) => onChange({ description: e.target.value })} rows={3} placeholder="Bu pipeline ne yapar?" />
      </Form.Item>
    </Form>
  </div>
);
