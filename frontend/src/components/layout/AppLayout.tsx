import React, { useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Badge } from 'antd';
import {
  DashboardOutlined, ApiOutlined, ApartmentOutlined,
  PlayCircleOutlined, SettingOutlined, UserOutlined,
  LogoutOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const navItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/connections', icon: <ApiOutlined />, label: 'Connections' },
  { key: '/pipelines', icon: <ApartmentOutlined />, label: 'Pipelines' },
  { key: '/jobs', icon: <PlayCircleOutlined />, label: 'Job Runs' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];

export const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, fetchMe } = useAuthStore();

  useEffect(() => {
    if (!user) fetchMe();
  }, []);

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: user?.full_name || 'Profile' },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: 'Çıkış Yap', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') logout();
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark" style={{ position: 'fixed', height: '100vh', left: 0, top: 0 }}>
        {/* Logo */}
        <div style={{ padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DatabaseOutlined style={{ fontSize: 24, color: '#1677ff' }} />
            <Text strong style={{ color: '#fff', fontSize: 16 }}>DataFlow</Text>
          </div>
          <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>ETL Platform</Text>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout style={{ marginLeft: 220 }}>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          position: 'sticky', top: 0, zIndex: 100,
        }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar size={32} icon={<UserOutlined />} style={{ background: '#1677ff' }} />
              <Text>{user?.full_name || 'Loading...'}</Text>
            </div>
          </Dropdown>
        </Header>

        <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};
