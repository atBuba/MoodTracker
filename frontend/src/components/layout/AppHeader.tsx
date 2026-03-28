import { Dropdown, Space, Typography } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../stores/authStore';
import NotificationBell from '../notifications/NotificationBell';

export default function AppHeader() {
  const { user, logout } = useAuthStore();

  const items = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Выйти',
      onClick: logout,
    },
  ];

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 24px' }}>
      <Typography.Title level={4} style={{ margin: 0, color: '#fff' }}>
        MoodTracker
      </Typography.Title>
      <Space size="large">
        {user?.role !== 'employee' && <NotificationBell />}
        <Dropdown menu={{ items }} placement="bottomRight">
          <Space style={{ cursor: 'pointer', color: '#fff' }}>
            <UserOutlined />
            <span>{user?.full_name}</span>
          </Space>
        </Dropdown>
      </Space>
    </div>
  );
}
