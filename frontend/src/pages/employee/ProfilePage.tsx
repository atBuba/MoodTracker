import { useState } from 'react';
import { Switch, message } from 'antd';
import { useAuthStore } from '../../stores/authStore';
import { updateMySettings } from '../../api/employees';

export default function ProfilePage() {
  const { user, loadUser } = useAuthStore();
  const [saving, setSaving] = useState(false);

  if (!user) return null;

  const handleToggle = async (checked: boolean) => {
    setSaving(true);
    try {
      await updateMySettings(checked);
      await loadUser();
      message.success('Настройки обновлены');
    } catch {
      message.error('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const initial = user.full_name.charAt(0).toUpperCase();

  return (
    <div>
      <div className="page-header">
        <h1>Мой профиль</h1>
        <p>Ваши данные и настройки</p>
      </div>

      <div className="detail-panel" style={{ maxWidth: 600 }}>
        <div className="detail-header">
          <div className="detail-avatar">{initial}</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 18 }}>{user.full_name}</div>
            <div style={{ color: '#999', fontSize: 14 }}>{user.email}</div>
          </div>
        </div>

        <div className="detail-row">
          <span className="label">Роль</span>
          <span className="value">{user.role === 'employee' ? 'Сотрудник' : user.role}</span>
        </div>
        <div className="detail-row">
          <span className="label">Сбор данных</span>
          <Switch
            checked={user.analysis_allowed}
            onChange={handleToggle}
            loading={saving}
          />
        </div>
      </div>
    </div>
  );
}
