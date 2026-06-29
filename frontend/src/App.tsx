import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import trTR from 'antd/locale/tr_TR';

import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { ConnectionsPage } from './pages/connections/ConnectionsPage';
import { PipelinesPage } from './pages/pipelines/PipelinesPage';
import { PipelineWizard } from './pages/pipelines/wizard/PipelineWizard';
import { JobRunsPage } from './pages/jobs/JobRunsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <ConfigProvider locale={trTR} theme={{ token: { colorPrimary: '#1677ff' } }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="connections" element={<ConnectionsPage />} />
            <Route path="pipelines" element={<PipelinesPage />} />
            <Route path="pipelines/new" element={<PipelineWizard />} />
            <Route path="jobs" element={<JobRunsPage />} />
            <Route path="settings" element={<div>Settings — yakında</div>} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  </QueryClientProvider>
);

export default App;
