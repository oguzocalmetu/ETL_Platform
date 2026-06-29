import React, { useEffect } from 'react';
import { Button, Select, Space, Table, Tag, Typography, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { schemaApi } from '../../../api/connections';
import type { WizardState } from './PipelineWizard';
import type { ColumnMapping } from '../../../types';

const { Title, Text } = Typography;

export const Step6ColumnMapping: React.FC<{ state: WizardState; onChange: (p: Partial<WizardState>) => void }> = ({ state, onChange }) => {
  const { data: srcCols = [], isLoading: srcLoading } = useQuery({
    queryKey: ['cols', state.source_connection_id, state.source_table],
    queryFn: () => schemaApi.getColumns(state.source_connection_id, state.source_table),
    enabled: !!(state.source_connection_id && state.source_table),
  });

  const { data: tgtCols = [], isLoading: tgtLoading } = useQuery({
    queryKey: ['cols', state.target_connection_id, state.target_table],
    queryFn: () => schemaApi.getColumns(state.target_connection_id, state.target_table),
    enabled: !!(state.target_connection_id && state.target_table),
  });

  // Auto-match on load
  useEffect(() => {
    if (srcCols.length > 0 && state.column_mappings.length === 0) {
      const autoMapped: ColumnMapping[] = srcCols.map((sc: any, i: number) => {
        const tgt = (tgtCols as any[]).find((tc) => tc.name === sc.name);
        return {
          source_column: sc.name,
          target_column: tgt?.name || sc.name,
          source_type: sc.data_type,
          target_type: tgt?.data_type || sc.data_type,
          is_constant: false,
          is_nullable: sc.is_nullable,
          is_excluded: false,
          ordinal_position: i,
          transform_rules: [],
        };
      });
      onChange({ column_mappings: autoMapped });
    }
  }, [srcCols, tgtCols]);

  const updateMapping = (index: number, partial: Partial<ColumnMapping>) => {
    const updated = [...state.column_mappings];
    updated[index] = { ...updated[index], ...partial };
    onChange({ column_mappings: updated });
  };

  const removeMapping = (index: number) => {
    const updated = state.column_mappings.filter((_, i) => i !== index);
    onChange({ column_mappings: updated.map((m, i) => ({ ...m, ordinal_position: i })) });
  };

  const addMapping = () => {
    onChange({
      column_mappings: [...state.column_mappings, {
        source_column: undefined, target_column: '',
        is_constant: false, is_nullable: true, is_excluded: false,
        ordinal_position: state.column_mappings.length, transform_rules: [],
      }],
    });
  };

  const columns = [
    {
      title: 'Kaynak Kolon', key: 'source', width: 220,
      render: (_: any, _r: ColumnMapping, i: number) => (
        <Select value={state.column_mappings[i]?.source_column} onChange={(v) => updateMapping(i, { source_column: v })}
          placeholder="Kaynak kolon" showSearch style={{ width: '100%' }} size="small">
          {(srcCols as any[]).map((c) => <Select.Option key={c.name} value={c.name}>{c.name} <Tag style={{ fontSize: 10 }}>{c.data_type}</Tag></Select.Option>)}
        </Select>
      ),
    },
    {
      title: 'Hedef Kolon', key: 'target', width: 220,
      render: (_: any, _r: ColumnMapping, i: number) => (
        <Select value={state.column_mappings[i]?.target_column || undefined} onChange={(v) => updateMapping(i, { target_column: v })}
          placeholder="Hedef kolon" showSearch style={{ width: '100%' }} size="small">
          {(tgtCols as any[]).map((c) => <Select.Option key={c.name} value={c.name}>{c.name} <Tag style={{ fontSize: 10 }}>{c.data_type}</Tag></Select.Option>)}
        </Select>
      ),
    },
    {
      title: 'İşlem', key: 'action', width: 80,
      render: (_: any, _r: ColumnMapping, i: number) => (
        <Button icon={<DeleteOutlined />} size="small" danger onClick={() => removeMapping(i)} />
      ),
    },
  ];

  if (srcLoading || tgtLoading) return <Spin tip="Schema yükleniyor..." />;

  return (
    <div>
      <Title level={4}>Kolon Eşleştirme</Title>
      <Text type="secondary">Kaynak ve hedef kolonları eşleştirin. Otomatik eşleştirme yapılmıştır.</Text>
      <div style={{ marginTop: 16 }}>
        <Table
          dataSource={state.column_mappings.map((m, i) => ({ ...m, _key: i }))}
          columns={columns} rowKey="_key" pagination={false} size="small"
          footer={() => <Button icon={<PlusOutlined />} onClick={addMapping} size="small">Eşleştirme Ekle</Button>}
        />
      </div>
    </div>
  );
};
