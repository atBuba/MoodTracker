import { useEffect } from 'react';
import { Badge } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useNotificationStore } from '../../stores/notificationStore';

export default function NotificationBell() {
  const { unreadCount, fetchUnreadCount } = useNotificationStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  return (
    <Badge count={unreadCount} size="small">
      <BellOutlined
        style={{ fontSize: 20, cursor: 'pointer' }}
        onClick={() => navigate('/notifications')}
      />
    </Badge>
  );
}
