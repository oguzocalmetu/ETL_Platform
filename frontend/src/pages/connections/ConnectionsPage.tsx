import React, { useState } from 'react';
import {
  Button, Card, Table, Space, Tag, Tooltip, Modal, Form, Input,
  Select, Typography, message, Popconfirm, Badge,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ThunderboltOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { connectionsApi } from '../../api/connections';
import type { Connection, ConnectionType } from '../../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

const CONNECTION_TYPES: ConnectionType[] = ['POSTGRESQL', 'MYSQL', 'MSSQL', 'CSV', 'EXCEL', 'SFTP'];

const TYPE_COLOR: Record<string, string> = {
  POSTGRESQL: 'blue', MYSQL: 'orange', MSSQL: 'geekblue',
  CSV: 'green', EXCEL: 'cyan', SFTP: 'purple',
};

export const ConnectionsPage: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingConn, setEditingConn] = useState<Connection | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; msg: string }>>({});
  const [form] = Form.useForm();
  const qc = useQueryClient();
  const [msgApi, contextHolder] = message.useMessage();

  const { data: connections = [], isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: () => connectionsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => editingConn
      ? connectionsApi.update(editingConn.id, data)
      : connectionsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['connections'] });
      setModalOpen(false);
      form.resetFields();
      setEditingConn(null);
      msgApi.success(editingConn ? 'Bağlantı güncellendi' : 'Bağlantı oluşturuldu');
    },
    onError: (e: any) => msgApi.error(e.response?.data?.detail || 'Hata oluştu'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => connectionsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['connections'] }); msgApi.success('Silindi'); },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => connectionsApi.test(id),
    onSuccess: (result, id) => {
      setTestResults((prev) => ({
        ...prev,
        [id]: { success: result.success, msg: result.success ? `${result.latency_ms}ms — ${result.server_version || 'OK'}` : (result.error || 'Hata') },
      }));
    },
  });

  const openCreate = () => { setEditingConn(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (conn: Connection) => {
    setEditingConn(conn);
    form.setFieldsValue({ ...conn, password: '' });
    setModalOpen(true);
  };

  const columns = [
    { title: 'Ad', dataIndex: 'name', key: 'name', render: (n: string) => <strong>{n}</strong> },
    {
      title: 'Tip', dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag color={TYPE_COLOR[t] || 'default'}>{t}</Tag>,
    },
    { title: 'Host / Yol', dataIndex: 'host', key: 'host', render: (h: string, r: Connection) => h || r.extra_config?.file_path || '—' },
    { title: 'Veritabanı', dataIndex: 'database_name', key: 'db', render: (d: string) => d || '—' },
    {
      title: 'Son Test', key: 'test_status',
      render: (_: any, r: Connection) => {
        const tr = testResults[r.id];
        if (tr) return tr.success
          ? <Badge status="success" text={<span style={{ color: '#52c41a', fontSize: 12 }}>{tr.msg}</span>} />
          : <Badge status="error" text={<span style={{ color: '#ff4d4f', fontSize: 12 }}>{tr.msg}</span>} />;
        if (r.last_test_status === 'SUCCESS') return <Badge status="success" text={dayjs(r.last_tested_at).format('DD/MM HH:mm')} />;
        if (r.last_test_status === 'FAILED') return <Badge status="error" text="Başarısız" />;
        return <Badge status="default" text="Test edilmedi" />;
      },
    },
    {
      title: 'İşlem', key: 'actions',
      render: (_: any, r: Connection) => (
        <Space>
          <Tooltip title="Bağlantı test et">
            <Button icon={<ThunderboltOutlined />} size="small" loading={testMutation.isPending}
              onClick={() => testMutation.mutate(r.id)} />
          </Tooltip>
          <Tooltip title="Düzenle">
            <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)} />
          </Tooltip>
          <Tooltip title="Sil">
            <Popconfirm title="Bu bağlantıyı silmek istediğinize emin misiniz?" onConfirm={() => deleteMutation.mutate(r.id)}>
              <Button icon={<DeleteOutlined />} size="small" danger />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {contextHolder}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Connections</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Yeni Bağlantı</Button>
      </div>

      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Table dataSource={connections} columns={columns} rowKey="id" loading={isLoading} />
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        title={editingConn ? 'Bağlantı Düzenle' : 'Yeni Bağlantı Oluştur'}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setEditingConn(null); }}
        footer={null}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={createMutation.mutate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="Bağlantı Adı" rules={[{ required: true }]}>
            <Input placeholder="sales_postgres" />
          </Form.Item>
          <Form.Item name="type" label="Tip" rules={[{ required: true }]}>
            <Select placeholder="Tip seçin">
              {CONNECTION_TYPES.map((t) => <Option key={t} value={t}>{t}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.type !== curr.type}>
            {({ getFieldValue }) => {
              const t = getFieldValue('type');
              if (['POSTGRESQL', 'MYSQL', 'MSSQL'].includes(t)) return (
                <>
                  <Form.Item name="host" label="Host" rules={[{ required: true }]}><Input placeholder="10.10.10.5" /></Form.Item>
                  <Form.Item name="port" label="Port"><Input type="number" placeholder="5432" /></Form.Item>
                  <Form.Item name="database_name" label="Veritabanı" rules={[{ required: true }]}><Input placeholder="my_database" /></Form.Item>
                  <Form.Item name="username" label="Kullanıcı Adı" rules={[{ required: true }]}><Input placeholder="etl_user" /></Form.Item>
                  <Form.Item name="password" label="Şifre"><Input.Password placeholder="••••••••" /></Form.Item>
                </>
              );
              if (t === 'CSV' || t === 'EXCEL') return (
                <Form.Item name={['extra_config', 'file_path']} label="Dosya Yolu" rules={[{ required: true }]}>
                  <Input placeholder="/data/myfile.csv" />
                </Form.Item>
              );
              return null;
            }}
          </Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={() => setModalOpen(false)}>İptal</Button>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              {editingConn ? 'Güncelle' : 'Oluştur'}
            </Button>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};
