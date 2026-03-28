import { useEffect, useState } from 'react';
import { Slider, Switch, message } from 'antd';
import { ExclamationCircleOutlined, BellOutlined } from '@ant-design/icons';
import type { ManagerSettings } from '../../types';
import { getSettings, updateSettings } from '../../api/settings';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const periodOptions = [
  { value: 'immediate', title: 'Немедленно', desc: 'Отправлять уведомление сразу при срабатывании' },
  { value: 'daily', title: 'Ежедневно', desc: 'Отправлять дайджест уведомлений раз в день' },
  { value: 'weekly', title: 'Еженедельно', desc: 'Собирать уведомления и отправлять раз в неделю' },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<ManagerSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch(() => message.error('Ошибка загрузки настроек'))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !settings) return <LoadingSpinner />;

  const save = async (patch: Partial<ManagerSettings>) => {
    const updated = { ...settings, ...patch };
    setSettings(updated);
    try {
      await updateSettings(patch);
      message.success('Настройки сохранены');
    } catch {
      message.error('Ошибка сохранения');
    }
  };

  const thresholdDisplay = Math.round(settings.threshold_value * 100);

  return (
    <div>
      <div className="page-header">
        <h1>Настройки системы</h1>
        <p>Управление порогами срабатывания и параметрами мониторинга</p>
      </div>

      <div className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon" style={{ background: '#fee2e2', color: '#ef4444' }}>
            <ExclamationCircleOutlined />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Пороги срабатывания</div>
            <div style={{ fontSize: 13, color: '#999' }}>Настройка уровней оповещения</div>
          </div>
        </div>

        <div className="threshold-label">
          <span>Критический уровень</span>
          <span className="threshold-value" style={{ color: '#ef4444' }}>{thresholdDisplay}</span>
        </div>
        <div style={{ background: '#fee2e2', borderRadius: 8, padding: '8px 16px' }}>
          <Slider
            min={10}
            max={90}
            value={thresholdDisplay}
            onChange={(v) => save({ threshold_value: v / 100 })}
            trackStyle={{ background: '#ef4444' }}
            handleStyle={{ borderColor: '#ef4444' }}
          />
        </div>
        <div className="threshold-hint">
          Индекс настроения ниже этого значения считается критическим и требует немедленного вмешательства
        </div>

        <div className="color-scale" />
        <div className="color-scale-labels">
          <span>0 (Критично)</span>
          <span>50 (Средне)</span>
          <span>100 (Отлично)</span>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon" style={{ background: '#f0e7ff', color: '#7c3aed' }}>
            <BellOutlined />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Настройки уведомлений</div>
            <div style={{ fontSize: 13, color: '#999' }}>Частота и способ отправки оповещений</div>
          </div>
        </div>

        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>Частота уведомлений</div>
        {periodOptions.map((opt) => (
          <div
            key={opt.value}
            className={`radio-option${settings.notification_period === opt.value ? ' selected' : ''}`}
            onClick={() => save({ notification_period: opt.value as ManagerSettings['notification_period'] })}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 18, height: 18, borderRadius: '50%',
                border: settings.notification_period === opt.value ? '5px solid #7c3aed' : '2px solid #ccc',
              }} />
              <div>
                <div className="radio-option-title">{opt.title}</div>
                <div className="radio-option-desc">{opt.desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="settings-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Автоматическая мотивация</div>
            <div style={{ fontSize: 13, color: '#999', marginTop: 4 }}>
              Автоматически отправлять мотивационный контент при падении настроения
            </div>
          </div>
          <Switch
            checked={settings.auto_motivation_enabled}
            onChange={(v) => save({ auto_motivation_enabled: v })}
          />
        </div>
      </div>
    </div>
  );
}
