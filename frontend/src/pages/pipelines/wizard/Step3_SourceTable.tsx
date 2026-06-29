import React, { useState } from 'react';
import { Form, Select, Input, Tabs, Button, Table, Typography, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { schemaApi } from '../../../api/connections';
import type { WizardState } from './PipelineWizard';

const { Title, Text } = Typography;

export const Step3SourceTable: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const [mode, setMode] = useState<'table' | 'query'>('table');
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const { data: tables = [], isLoading } = useQuery({
    queryKey: ['tables', state.source_connection_id],
    queryFn: () => schemaApi.listTables(state.source_connection_id),
    enabled: !!state.source_connection_id,
  });

  const handlePreview = async () => {
    if (!state.source_table) return;
    setPreviewLoading(true);
    try {
      const data = await schemaApi.preview(state.source_connection_id, state.source_table);
      setPreviewData(data);
    } finally { setPreviewLoading(false); }
  };

  return (
    <div>
      <Title level={4}>Kaynak Tablo / Sorgu</Title>
      <Tabs activeKey={mode} onChange={(k) => setMode(k as any)} items={[
        { key: 'table', label: 'Tablo Seç' },
        { key: 'query', label: 'Custom SQL' },
      ]} />
      {mode === 'table' ? (
        <Form layout="vertical" style={{ maxWidth: 480 }}>
          <Form.Item label="Tablo" required>
            <Select value={state.source_table || undefined} onChange={(v) => onChange({ source_table: v })}
              loading={isLoading} placeholder="Tablo seçin" showSearch>
              {tables.map((t: string) => <Select.Option key={t} value={t}>{t}</Select.Option>)}
            </Select>
          </Form.Item>
          {state.source_table && <Button onClick={handlePreview} loading={previewLoading}>Önizle (20 satır)</Button>}
        </Form>
      ) : (
        <Form layout="vertical">
          <Form.Item label="SQL Sorgusu">
            <Input.TextArea value={state.source_query} onChange={(e) => onChange({ source_query: e.target.value })}
              rows={5} placeholder="SELECT * FROM orders WHERE status = 'active'" style={{ fontFamily: 'monospace' }} />
          </Form.Item>
        </Form>
      )}
      {previewData && (
        <Table size="small" style={{ marginTop: 16 }} scroll={{ x: true }}
          dataSource={previewData.rows.map((r: any, i: number) => ({ ...r, _key: i }))}
          columns={previewData.columns.map((c: string) => ({ title: c, dataIndex: c, key: c, ellipsis: true, width: 120 }))}
          rowKey="_key" pagination={false} />
      )}
    </div>
  );
};
