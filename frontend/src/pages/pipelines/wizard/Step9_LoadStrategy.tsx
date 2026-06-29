import React from 'react';
import { Form, Select, InputNumber, Typography, Alert } from 'antd';
import type { WizardState } from './PipelineWizard';
const { Title, Text } = Typography;
const STRATEGIES = [
  { value: 'FULL_LOAD', label: 'Full Load', desc: 'Önce tablo boşaltılır, tüm veri yeniden yazılır.' },
  { value: 'APPEND', label: 'Append', desc: 'Mevcut verilere ek olarak yeni satırlar eklenir.' },
  { value: 'TRUNCATE_INSERT', label: 'Truncate + Insert', desc: 'Tablo truncate edilir, yeni veri eklenir.' },
  { value: 'UPSERT', label: 'Upsert / Merge', desc: 'Anahtar kolonlara göre güncelleme veya ekleme yapılır.' },
  { value: 'INCREMENTAL', label: 'Incremental Load', desc: 'Checkpoint kolonuna göre sadece yeni/değişen kayıtlar alınır.' },
];
export const Step9LoadStrategy: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const selected = STRATEGIES.find((s) => s.value === state.load_strategy);
  return (
    <div>
      <Title level={4}>Load Strategy</Title>
      <Form layout="vertical" style={{ maxWidth: 480, marginTop: 16 }}>
        <Form.Item label="Strateji" required>
          <Select value={state.load_strategy} onChange={(v) => onChange({ load_strategy: v })}>
            {STRATEGIES.map((s) => <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>)}
          </Select>
        </Form.Item>
        {selected && <Alert type="info" message={selected.desc} showIcon style={{ marginBottom: 16 }} />}
        <Form.Item label="Batch Boyutu">
          <InputNumber min={100} max={1000000} value={state.batch_size} onChange={(v) => onChange({ batch_size: v || 10000 })} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </div>
  );
};
