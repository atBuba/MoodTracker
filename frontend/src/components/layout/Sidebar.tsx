import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppstoreOutlined,
  TeamOutlined,
  BellOutlined,
  FileTextOutlined,
  SettingOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Dropdown } from 'antd';
import { useAuthStore } from '../../stores/authStore';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const managerItems = [
    { key: '/dashboard', icon: <AppstoreOutlined />, label: 'Дашборд' },
    { key: '/employees', icon: <TeamOutlined />, label: 'Сотрудники' },
    { key: '/notifications', icon: <BellOutlined />, label: 'Уведомления' },
    { key: '/content', icon: <FileTextOutlined />, label: 'Контент' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Настройки' },
  ];

  const employeeItems = [
    { key: '/my-dashboard', icon: <DashboardOutlined />, label: 'Мой дашборд' },
    { key: '/my-profile', icon: <UserOutlined />, label: 'Профиль' },
  ];

  const items = user?.role === 'employee' ? employeeItems : managerItems;
  const initial = user?.full_name?.charAt(0)?.toUpperCase() ?? '?';

  const dropdownItems = [
    { key: 'logout', icon: <LogoutOutlined />, label: 'Выйти', onClick: logout },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <AppstoreOutlined />
        </div>
        <div className="sidebar-logo-text">
          <h3>BurnOutDetector</h3>
          <span>Мониторинг благополучия</span>
        </div>
      </div>

      <div className="sidebar-menu">
        {items.map((item) => (
          <div
            key={item.key}
            className={`sidebar-item${location.pathname.startsWith(item.key) ? ' active' : ''}`}
            onClick={() => navigate(item.key)}
          >
            {item.icon}
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <Dropdown menu={{ items: dropdownItems }} placement="topRight" trigger={['click']}>
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">{initial}</div>
          <div className="sidebar-user-info">
            <div className="name">{user?.full_name}</div>
            <div className="role">{user?.role === 'manager' ? 'Менеджер' : user?.role === 'admin' ? 'Админ' : 'Сотрудник'}</div>
          </div>
        </div>
      </Dropdown>
    </div>
  );
}
