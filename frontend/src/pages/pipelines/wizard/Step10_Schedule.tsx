import React from 'react';
import { Form, Select, Input, Switch, Alert, Space, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import type { WizardState } from './PipelineWizard';

interface Props {
  state: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}

const CRON_PRESETS = [
  { value: '0 * * * *', label: 'Her saat başı' },
  { value: '0 6 * * *', label: 'Her gün sabah 06:00' },
  { value: '0 0 * * *', label: 'Her gün gece 00:00' },
  { value: '0 6 * * 1', label: 'Her Pazartesi sabah 06:00' },
  { value: '0 6 1 * *', label: 'Her ayın 1\'i sabah 06:00' },
  { value: 'custom', label: 'Özel cron ifadesi' },
];

const Step10_Schedule: React.FC<Props> = ({ state, onChange }) => {
  const schedule = state.schedule ?? { enabled: false, cron_expr: '0 6 * * *' };
  const [preset, setPreset] = React.useState(
    CRON_PRESETS.find(p => p.value === schedule.cron_expr)?.value ?? 'custom'
  );

  const updateSchedule = (patch: Partial<typeof schedule>) => {
    onChange({ schedule: { ...schedule, ...patch } });
  };

  return (
    <div>
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: 20 }}
        message="Zamanlama isteğe bağlıdır. Pipeline'ı manuel olarak da çalıştırabilirsiniz."
      />

      <Form layout="vertical">
        <Form.Item label="Otomatik zamanlama aktif">
          <Switch
            checked={schedule.enabled}
            onChange={v => updateSchedule({ enabled: v })}
            checkedChildren="Açık"
            unCheckedChildren="Kapalı"
          />
        </Form.Item>

        {schedule.enabled && (
          <>
            <Form.Item label="Zamanlama sıklığı">
              <Select
                value={preset}
                onChange={v => {
                  setPreset(v);
                  if (v !== 'custom') updateSchedule({ cron_expr: v });
                }}
                options={CRON_PRESETS}
              />
            </Form.Item>

            {preset === 'custom' && (
              <Form.Item
                label="Cron ifadesi"
                help="Örnek: '0 6 * * 1-5' (hafta içi her sabah 06:00)"
              >
                <Input
                  value={schedule.cron_expr}
                  onChange={e => updateSchedule({ cron_expr: e.target.value })}
                  placeholder="0 6 * * *"
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>
            )}

            <div
              style={{
                padding: '10px 14px',
                background: '#f6ffed',
                border: '1px solid #b7eb8f',
                borderRadius: 6,
                marginTop: 8,
              }}
            >
              <Space direction="vertical" size={2}>
                <Typography.Text strong style={{ fontSize: 12 }}>
                  Cron: <code>{schedule.cron_expr}</code>
                </Typography.Text>
                <Typography.Text style={{ fontSize: 12, color: '#52c41a' }}>
                  {CRON_PRESETS.find(p => p.value === schedule.cron_expr)?.label ??
                    'Özel zamanlama'}
                </Typography.Text>
              </Space>
            </div>
          </>
        )}
      </Form>
    </div>
  );
};

export default Step10_Schedule;
