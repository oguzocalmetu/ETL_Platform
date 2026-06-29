import React, { useState } from 'react';
import { Button, Select, Input, Table, Space, Tag, Tooltip, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { WizardState } from './PipelineWizard';

interface Props {
  state: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}

const TRANSFORM_OPTIONS = [
  { value: 'TRIM', label: 'TRIM — Baş/sondaki boşlukları sil' },
  { value: 'UPPER', label: 'UPPER — Büyük harfe çevir' },
  { value: 'LOWER', label: 'LOWER — Küçük harfe çevir' },
  { value: 'CAST', label: 'CAST — Tip dönüşümü' },
  { value: 'TO_DATE', label: 'TO_DATE — Tarihe çevir' },
  { value: 'TO_TIMESTAMP', label: 'TO_TIMESTAMP — Zaman damgasına çevir' },
  { value: 'REPLACE', label: 'REPLACE — Değer değiştir' },
  { value: 'SUBSTRING', label: 'SUBSTRING — Alt dize al' },
  { value: 'COALESCE', label: 'COALESCE — Null ise varsayılan kullan' },
  { value: 'NULL_HANDLING', label: 'NULL_HANDLING — Null değerleri yönet' },
];

const Step7_TransformRules: React.FC<Props> = ({ state, onChange }) => {
  const [newRule, setNewRule] = useState({ column: '', transform_type: '', params: '' });

  const rules = state.transformRules ?? [];
  const mappedColumns = (state.columnMappings ?? [])
    .filter(m => m.target_column)
    .map(m => m.target_column as string);

  const addRule = () => {
    if (!newRule.column || !newRule.transform_type) return;
    onChange({
      transformRules: [
        ...rules,
        { ...newRule, params: newRule.params ? JSON.parse(`{"value":"${newRule.params}"}`) : {} },
      ],
    });
    setNewRule({ column: '', transform_type: '', params: '' });
  };

  const removeRule = (idx: number) => {
    onChange({ transformRules: rules.filter((_, i) => i !== idx) });
  };

  const columns = [
    { title: 'Kolon', dataIndex: 'column', key: 'column', render: (v: string) => <Tag>{v}</Tag> },
    {
      title: 'Dönüşüm',
      dataIndex: 'transform_type',
      key: 'transform_type',
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: 'Parametreler',
      dataIndex: 'params',
      key: 'params',
      render: (v: object) => (
        <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{JSON.stringify(v)}</span>
      ),
    },
    {
      title: '',
      key: 'action',
      render: (_: unknown, __: unknown, idx: number) => (
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => removeRule(idx)} />
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, color: 'rgba(0,0,0,0.45)', fontSize: 13 }}>
        <InfoCircleOutlined /> Kolon eşleştirmesinden sonra uygulanacak dönüşüm kurallarını
        tanımlayın. Bu adım isteğe bağlıdır.
      </div>

      <Space style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <Select
          placeholder="Kolon seçin"
          style={{ width: 180 }}
          value={newRule.column || undefined}
          onChange={v => setNewRule(r => ({ ...r, column: v }))}
          options={mappedColumns.map(c => ({ value: c, label: c }))}
        />
        <Select
          placeholder="Dönüşüm tipi"
          style={{ width: 220 }}
          value={newRule.transform_type || undefined}
          onChange={v => setNewRule(r => ({ ...r, transform_type: v }))}
          options={TRANSFORM_OPTIONS}
        />
        <Tooltip title="Format, değer vb. isteğe bağlı parametre">
          <Input
            placeholder="Parametre (opsiyonel)"
            style={{ width: 160 }}
            value={newRule.params}
            onChange={e => setNewRule(r => ({ ...r, params: e.target.value }))}
          />
        </Tooltip>
        <Button type="primary" icon={<PlusOutlined />} onClick={addRule}>
          Ekle
        </Button>
      </Space>

      {rules.length > 0 ? (
        <Table
          dataSource={rules.map((r, i) => ({ ...r, key: i }))}
          columns={columns}
          size="small"
          pagination={false}
        />
      ) : (
        <Empty description="Henüz dönüşüm kuralı yok — bu adım isteğe bağlıdır" />
      )}
    </div>
  );
};

export default Step7_TransformRules;
