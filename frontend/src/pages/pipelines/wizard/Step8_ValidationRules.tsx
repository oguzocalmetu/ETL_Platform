import React, { useState } from 'react';
import { Button, Select, Input, Table, Tag, Space, Alert, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { WizardState } from './PipelineWizard';

interface Props {
  state: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}

const RULE_TYPES = [
  { value: 'NOT_NULL', label: 'NOT_NULL — Boş olamaz' },
  { value: 'UNIQUE', label: 'UNIQUE — Benzersiz olmalı' },
  { value: 'REGEX', label: 'REGEX — Regex pattern eşleşmeli' },
  { value: 'RANGE', label: 'RANGE — Sayısal aralık kontrolü' },
  { value: 'DATE_FORMAT', label: 'DATE_FORMAT — Tarih formatı' },
];

const ACTIONS = [
  { value: 'REJECT', label: 'REJECT — Satırı reddet, devam et' },
  { value: 'WARN', label: 'WARN — Uyar, devam et' },
  { value: 'STOP', label: 'STOP — Tüm job\'u durdur' },
];

const Step8_ValidationRules: React.FC<Props> = ({ state, onChange }) => {
  const [newRule, setNewRule] = useState({
    column: '',
    rule_type: '',
    action: 'REJECT',
    params: '',
  });

  const rules = state.validationRules ?? [];
  const mappedColumns = (state.columnMappings ?? [])
    .filter(m => m.target_column)
    .map(m => m.target_column as string);

  const addRule = () => {
    if (!newRule.column || !newRule.rule_type) return;
    onChange({
      validationRules: [
        ...rules,
        {
          column: newRule.column,
          rule_type: newRule.rule_type,
          action: newRule.action,
          params: newRule.params ? { pattern: newRule.params } : {},
        },
      ],
    });
    setNewRule({ column: '', rule_type: '', action: 'REJECT', params: '' });
  };

  const removeRule = (idx: number) => {
    onChange({ validationRules: rules.filter((_, i) => i !== idx) });
  };

  const actionColor: Record<string, string> = {
    REJECT: 'orange',
    WARN: 'gold',
    STOP: 'red',
  };

  const columns = [
    { title: 'Kolon', dataIndex: 'column', key: 'col', render: (v: string) => <Tag>{v}</Tag> },
    {
      title: 'Kural',
      dataIndex: 'rule_type',
      key: 'rt',
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: 'Aksiyon',
      dataIndex: 'action',
      key: 'act',
      render: (v: string) => <Tag color={actionColor[v]}>{v}</Tag>,
    },
    {
      title: 'Parametre',
      dataIndex: 'params',
      key: 'p',
      render: (v: object) => (
        <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{JSON.stringify(v)}</span>
      ),
    },
    {
      title: '',
      key: 'del',
      render: (_: unknown, __: unknown, idx: number) => (
        <Button danger size="small" icon={<DeleteOutlined />} onClick={() => removeRule(idx)} />
      ),
    },
  ];

  return (
    <div>
      <Alert
        type="info"
        style={{ marginBottom: 16 }}
        message="Doğrulama kuralları isteğe bağlıdır. REJECT: geçersiz satırlar ayrı tabloya kaydedilir, aktarım devam eder. STOP: ilk hata tüm job'u durdurur."
        showIcon
      />

      <Space style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <Select
          placeholder="Kolon seçin"
          style={{ width: 160 }}
          value={newRule.column || undefined}
          onChange={v => setNewRule(r => ({ ...r, column: v }))}
          options={mappedColumns.map(c => ({ value: c, label: c }))}
        />
        <Select
          placeholder="Kural tipi"
          style={{ width: 200 }}
          value={newRule.rule_type || undefined}
          onChange={v => setNewRule(r => ({ ...r, rule_type: v }))}
          options={RULE_TYPES}
        />
        <Select
          style={{ width: 160 }}
          value={newRule.action}
          onChange={v => setNewRule(r => ({ ...r, action: v }))}
          options={ACTIONS}
        />
        <Input
          placeholder="Parametre (regex, min:max vb.)"
          style={{ width: 180 }}
          value={newRule.params}
          onChange={e => setNewRule(r => ({ ...r, params: e.target.value }))}
        />
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
        <Empty description="Henüz doğrulama kuralı yok" />
      )}
    </div>
  );
};

export default Step8_ValidationRules;
