import React, { useState } from 'react';
import { Steps, Card, Button, Space, message, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { pipelinesApi } from '../../../api/pipelines';
import type { Pipeline, ColumnMapping, ValidationRule } from '../../../types';

// Step components
import { Step1BasicInfo } from './Step1_BasicInfo';
import { Step2SourceConnection } from './Step2_SourceConnection';
import { Step3SourceTable } from './Step3_SourceTable';
import { Step4TargetConnection } from './Step4_TargetConnection';
import { Step5TargetTable } from './Step5_TargetTable';
import { Step6ColumnMapping } from './Step6_ColumnMapping';
import Step7TransformRules from './Step7_TransformRules';
import Step8ValidationRules from './Step8_ValidationRules';
import { Step9LoadStrategy } from './Step9_LoadStrategy';
import Step10Schedule from './Step10_Schedule';
import { Step11Review } from './Step11_Review';

const { Title } = Typography;

const STEPS = [
  { title: 'Temel Bilgiler' },
  { title: 'Kaynak Bağlantı' },
  { title: 'Kaynak Tablo' },
  { title: 'Hedef Bağlantı' },
  { title: 'Hedef Tablo' },
  { title: 'Kolon Eşleştirme' },
  { title: 'Dönüşümler' },
  { title: 'Validation' },
  { title: 'Load Strategy' },
  { title: 'Schedule' },
  { title: 'Özet & Publish' },
];

export interface WizardState {
  name: string;
  description: string;
  source_connection_id: string;
  source_table: string;
  source_query: string;
  target_connection_id: string;
  target_table: string;
  load_strategy: string;
  batch_size: number;
  column_mappings: ColumnMapping[];
  columnMappings?: ColumnMapping[];       // alias for step components
  validation_rules: ValidationRule[];
  validationRules?: ValidationRule[];     // alias for step components
  transformRules?: any[];
  schedule?: { enabled: boolean; cron_expr: string };
  created_pipeline_id?: string;
}

export const PipelineWizard: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [msgApi, contextHolder] = message.useMessage();

  const [state, setState] = useState<WizardState>({
    name: '',
    description: '',
    source_connection_id: '',
    source_table: '',
    source_query: '',
    target_connection_id: '',
    target_table: '',
    load_strategy: 'FULL_LOAD',
    batch_size: 10000,
    column_mappings: [],
    columnMappings: [],
    validation_rules: [],
    validationRules: [],
    transformRules: [],
    schedule: { enabled: false, cron_expr: '0 6 * * *' },
  });

  const updateState = (partial: Partial<WizardState>) =>
    setState((prev) => {
      const next = { ...prev, ...partial };
      // Keep aliases in sync
      if (partial.columnMappings !== undefined) next.column_mappings = partial.columnMappings;
      if (partial.column_mappings !== undefined) next.columnMappings = partial.column_mappings;
      if (partial.validationRules !== undefined) next.validation_rules = partial.validationRules;
      if (partial.validation_rules !== undefined) next.validationRules = partial.validation_rules;
      return next;
    });

  const next = () => setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1));
  const prev = () => setCurrentStep((s) => Math.max(s - 1, 0));

  const handlePublish = async () => {
    setLoading(true);
    try {
      let pipelineId = state.created_pipeline_id;
      if (!pipelineId) {
        const pipeline = await pipelinesApi.create({
          name: state.name,
          description: state.description,
          source_connection_id: state.source_connection_id,
          target_connection_id: state.target_connection_id,
          source_config: { table: state.source_table, query: state.source_query || undefined },
          target_config: { table: state.target_table },
          load_strategy: state.load_strategy as any,
          batch_size: state.batch_size,
        });
        pipelineId = pipeline.id;
        updateState({ created_pipeline_id: pipelineId });
      }

      if (state.column_mappings.length > 0) {
        await pipelinesApi.saveMappings(pipelineId, state.column_mappings);
      }

      if (state.validation_rules.length > 0) {
        await pipelinesApi.saveValidations(pipelineId, state.validation_rules);
      }

      await pipelinesApi.publish(pipelineId);

      msgApi.success('Pipeline başarıyla yayınlandı!');
      navigate('/pipelines');
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail || 'Pipeline oluşturulamadı');
    } finally {
      setLoading(false);
    }
  };

  const stepComponents = [
    <Step1BasicInfo state={state} onChange={updateState} />,
    <Step2SourceConnection state={state} onChange={updateState} />,
    <Step3SourceTable state={state} onChange={updateState} />,
    <Step4TargetConnection state={state} onChange={updateState} />,
    <Step5TargetTable state={state} onChange={updateState} />,
    <Step6ColumnMapping state={state} onChange={updateState} />,
    <Step7TransformRules state={state} onChange={updateState} />,
    <Step8ValidationRules state={state} onChange={updateState} />,
    <Step9LoadStrategy state={state} onChange={updateState} />,
    <Step10Schedule state={state} onChange={updateState} />,
    <Step11Review state={state} onPublish={handlePublish} loading={loading} />,
  ];

  return (
    <div>
      {contextHolder}
      <Title level={3} style={{ marginBottom: 24 }}>Yeni Pipeline Oluştur</Title>

      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}>
        <Steps current={currentStep} items={STEPS} size="small" />
      </Card>

      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)', minHeight: 400 }}>
        {stepComponents[currentStep]}
      </Card>

      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={() => navigate('/pipelines')}>İptal</Button>
        <Space>
          {currentStep > 0 && <Button onClick={prev}>Geri</Button>}
          {currentStep < STEPS.length - 1 && (
            <Button type="primary" onClick={next}>İleri</Button>
          )}
        </Space>
      </div>
    </div>
  );
};
