import { useEffect, useState } from 'react';
import { Input, Select, message } from 'antd';
import { SearchOutlined, UserOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { User } from '../../types';
import { getEmployees } from '../../api/employees';
import { displayMood, getRiskLevel, getTrendIcon } from '../../utils/moodColor';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<User | null>(null);
  const [search, setSearch] = useState('');
  const [_riskFilter, setRiskFilter] = useState<string | undefined>();

  useEffect(() => {
    getEmployees({ per_page: 50 })
      .then((res) => setEmployees(res.data))
      .catch(() => message.error('Ошибка загрузки'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const filtered = employees.filter((e) =>
    e.full_name.toLowerCase().includes(search.toLowerCase()) ||
    e.email.toLowerCase().includes(search.toLowerCase())
  );

  const total = filtered.length;
  const initial = (name: string) => name.charAt(0).toUpperCase();
  const mood = displayMood(0.6); // placeholder since backend doesn't return mood on user list
  const risk = getRiskLevel(0.6);
  const trend = getTrendIcon(null);

  return (
    <div>
      <div className="page-header">
        <h1>Мониторинг сотрудников</h1>
        <p>Отслеживание состояния и рисков выгорания</p>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder="Поиск по имени или email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, borderRadius: 10, height: 44 }}
        />
        <Select
          placeholder="Все уровни риска"
          allowClear
          onChange={setRiskFilter}
          style={{ width: 200 }}
          options={[
            { value: 'critical', label: 'Критический' },
            { value: 'high', label: 'Высокий' },
            { value: 'medium', label: 'Средний' },
            { value: 'low', label: 'Низкий' },
          ]}
        />
      </div>

      <div className="stat-cards">
        <div className="stat-card active">
          <div className="stat-card-label">Всего</div>
          <div className="stat-card-value">{total}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #ef4444' }}>
          <div className="stat-card-label" style={{ color: '#ef4444' }}>Критический</div>
          <div className="stat-card-value" style={{ color: '#ef4444' }}>0</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #ea580c' }}>
          <div className="stat-card-label" style={{ color: '#ea580c' }}>Высокий</div>
          <div className="stat-card-value" style={{ color: '#ea580c' }}>0</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #f59e0b' }}>
          <div className="stat-card-label" style={{ color: '#f59e0b' }}>Средний</div>
          <div className="stat-card-value" style={{ color: '#f59e0b' }}>0</div>
        </div>
      </div>

      <div className="employees-layout">
        <div>
          {filtered.map((emp) => (
            <div
              key={emp.id}
              className={`employee-card${selected?.id === emp.id ? ' selected' : ''}`}
              onClick={() => setSelected(emp)}
            >
              <div className="employee-avatar">{initial(emp.full_name)}</div>
              <div className="employee-info">
                <div className="employee-name">{emp.full_name}</div>
                <div className="employee-dept">{emp.email}</div>
                <span className={`risk-badge ${risk.className}`}>{risk.label}</span>
                <div className="employee-meta">Роль: {emp.role}</div>
              </div>
              <div className="employee-mood">
                <div className="employee-mood-value">
                  <span style={{ color: trend.color, fontSize: 14 }}>{trend.icon}</span>
                  {mood}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div>
          {selected ? (
            <div className="detail-panel">
              <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 20 }}>Детали сотрудника</h3>
              <div className="detail-header">
                <div className="detail-avatar">{initial(selected.full_name)}</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 16 }}>{selected.full_name}</div>
                  <div style={{ color: '#999', fontSize: 13 }}>{selected.email}</div>
                </div>
              </div>

              <div className="detail-row">
                <span className="label">Индекс настроения</span>
                <span className="value">{mood}</span>
              </div>
              <div className="detail-row">
                <span className="label">Уровень риска</span>
                <span className={`risk-badge ${risk.className}`}>{risk.label}</span>
              </div>
              <div className="detail-row">
                <span className="label">Сбор данных</span>
                <span className={`risk-badge ${selected.analysis_allowed ? 'low' : 'critical'}`}>
                  {selected.analysis_allowed ? 'Активен' : 'Отключён'}
                </span>
              </div>

              <div style={{ marginTop: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <InfoCircleOutlined style={{ color: '#7c3aed' }} />
                  <span style={{ fontWeight: 600 }}>Рекомендации для менеджера</span>
                </div>
                {[
                  'Свяжитесь с сотрудником для индивидуальной беседы',
                  'Рассмотрите возможность перераспределения задач',
                  'Предложите дополнительный выходной или отгул',
                  'Обсудите возможность временного снижения нагрузки',
                ].map((text, i) => (
                  <div className="recommendation-item" key={i}>
                    <div className="recommendation-num">{i + 1}</div>
                    <span>{text}</span>
                  </div>
                ))}
              </div>

              <button className="btn-primary" style={{ marginTop: 20 }}>Отправить поддержку</button>
              <button className="btn-outline">Запланировать встречу</button>
            </div>
          ) : (
            <div className="empty-state">
              <UserOutlined />
              <span>Выберите сотрудника для просмотра деталей и рекомендаций</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
