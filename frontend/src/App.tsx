import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import { useAuthStore } from './stores/authStore';
import AppLayout from './components/layout/AppLayout';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import ManagerDashboard from './pages/manager/DashboardPage';
import EmployeesPage from './pages/manager/EmployeesPage';

import NotificationsPage from './pages/manager/NotificationsPage';
import SettingsPage from './pages/manager/SettingsPage';
import ContentPage from './pages/manager/ContentPage';
import EmployeeDashboard from './pages/employee/DashboardPage';
import ProfilePage from './pages/employee/ProfilePage';

export default function App() {
  const { isAuthenticated, loadUser } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) loadUser();
  }, [isAuthenticated, loadUser]);

  return (
    <ConfigProvider locale={ruRU}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            {/* Manager routes */}
            <Route path="/dashboard" element={<ProtectedRoute roles={['manager', 'admin']}><ManagerDashboard /></ProtectedRoute>} />
            <Route path="/employees" element={<ProtectedRoute roles={['manager', 'admin']}><EmployeesPage /></ProtectedRoute>} />

            <Route path="/notifications" element={<ProtectedRoute roles={['manager', 'admin']}><NotificationsPage /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute roles={['manager', 'admin']}><SettingsPage /></ProtectedRoute>} />
            <Route path="/content" element={<ProtectedRoute roles={['manager', 'admin']}><ContentPage /></ProtectedRoute>} />
            {/* Employee routes */}
            <Route path="/my-dashboard" element={<ProtectedRoute roles={['employee']}><EmployeeDashboard /></ProtectedRoute>} />
            <Route path="/my-profile" element={<ProtectedRoute roles={['employee']}><ProfilePage /></ProtectedRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
