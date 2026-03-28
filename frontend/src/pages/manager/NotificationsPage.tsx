import { useEffect, useState } from 'react';
import { message } from 'antd';
import {
  ExclamationCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import type { Notification, PaginationMeta } from '../../types';
import { getNotifications, markAsRead } from '../../api/notifications';
import { useNotificationStore } from '../../stores/notificationStore';
import { formatDateTime } from '../../utils/formatDate';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  const [meta, setMeta] = useState<PaginationMeta>({ total: 0, page: 1, per_page: 20 });
  const [loading, setLoading] = useState(true);
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);

  const fetchData = (page = 1) => {
    setLoading(true);
    getNotifications({ page })
      .then((res) => { setItems(res.data); setMeta(res.meta); })
      .catch(() => message.error('Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleMarkRead = async (id: string) => {
    await markAsRead(id);
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    fetchUnreadCount();
  };

  const handleMarkAll = async () => {
    const unread = items.filter((n) => !n.is_read);
    for (const n of unread) {
      await markAsRead(n.id);
    }
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    fetchUnreadCount();
  };

  if (loading) return <LoadingSpinner />;

  const unreadCount = items.filter((n) => !n.is_read).length;
  const criticalCount = items.filter((n) => n.type === 'alert').length;
  const warningCount = items.filter((n) => n.type === 'report').length;

  const initial = (title: string) => title.charAt(0).toUpperCase();

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h1>Уведомления</h1>
          <p>{unreadCount} непрочитанных уведомлений</p>
        </div>
        {unreadCount > 0 && (
          <button
            className="btn-primary"
            style={{ width: 'auto', padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 8 }}
            onClick={handleMarkAll}
          >
            <CheckOutlined /> Отметить все как прочитанные
          </button>
        )}
      </div>

      <div className="stat-cards">
        <div className="stat-card active">
          <div className="stat-card-label">Всего</div>
          <div className="stat-card-value">{meta.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Непрочитанные</div>
          <div className="stat-card-value">{unreadCount}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #ef4444' }}>
          <div className="stat-card-label" style={{ color: '#ef4444' }}>Критические</div>
          <div className="stat-card-value" style={{ color: '#ef4444' }}>{criticalCount}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #f59e0b' }}>
          <div className="stat-card-label" style={{ color: '#f59e0b' }}>Предупреждения</div>
          <div className="stat-card-value" style={{ color: '#f59e0b' }}>{warningCount}</div>
        </div>
      </div>

      {items.map((item) => {
        const isCritical = item.type === 'alert';
        return (
          <div className="notification-card" key={item.id}>
            <div className={`notif-icon ${isCritical ? 'critical' : 'warning'}`}>
              {isCritical ? <ExclamationCircleOutlined /> : <WarningOutlined />}
            </div>
            <div className="notif-body">
              <div className="notif-top">
                <span className={`risk-badge ${isCritical ? 'critical' : 'medium'}`}>
                  {isCritical ? 'Критическое' : 'Предупреждение'}
                </span>
                {!item.is_read && <span className="notif-unread-dot" />}
              </div>
              <div className="notif-user">
                <div className="notif-user-avatar">{initial(item.title)}</div>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{item.title}</span>
              </div>
              <div style={{ fontSize: 14, color: '#555' }}>{item.content}</div>
              <div className="notif-time">
                <ClockCircleOutlined /> {formatDateTime(item.created_at)}
              </div>
            </div>
            {!item.is_read ? (
              <span className="notif-action" onClick={() => handleMarkRead(item.id)}>
                Отметить прочитанным
              </span>
            ) : (
              <span className="notif-action read">Прочитано</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
