import { useEffect, useState } from 'react';
import { message } from 'antd';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import {
  LineChartOutlined,
  ExclamationCircleOutlined,
  TeamOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { ManagerDashboard } from '../../types';
import { getManagerDashboard } from '../../api/dashboard';
import { formatShortDate } from '../../utils/formatDate';
import { displayMood } from '../../utils/moodColor';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const PIE_COLORS = ['#22c55e', '#f59e0b', '#ea580c', '#ef4444'];

export default function DashboardPage() {
  const [data, setData] = useState<ManagerDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getManagerDashboard()
      .then(setData)
      .catch(() => message.error('Ошибка загрузки дашборда'))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return <LoadingSpinner />;

  const avgDisplay = displayMood(data.avg_mood_index) ?? 0;
  const riskCount = data.at_risk_employees.length;
  const trendData = data.mood_trend_30d.map((p) => ({
    ...p,
    mood_index: displayMood(p.mood_index) ?? 0,
  }));

  // Generate pie data from risk employees
  const pieData = [
    { name: 'Низкий', value: Math.max(0, data.total_employees - riskCount) },
    { name: 'Средний', value: data.at_risk_employees.filter((e) => e.mood_index >= 0.5).length },
    { name: 'Высокий', value: data.at_risk_employees.filter((e) => e.mood_index >= 0.3 && e.mood_index < 0.5).length },
    { name: 'Критический', value: data.at_risk_employees.filter((e) => e.mood_index < 0.3).length },
  ].filter((d) => d.value > 0);

  const today = new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  return (
    <div>
      <div className="page-header">
        <h1>Дашборд мониторинга благополучия</h1>
        <p>Обзор состояния сотрудников и команд &bull; {today}</p>
      </div>

      <div className="info-banner">
        <span role="img" aria-label="wave">👋</span> Вы вошли как Менеджер. Вы видите данные по своим командам.
      </div>

      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-card-label">Средний индекс</div>
          <div className="stat-card-value">{avgDisplay}</div>
          <div className="stat-card-icon" style={{ background: '#f0e7ff', color: '#7c3aed' }}>
            <LineChartOutlined />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">В зоне риска</div>
          <div className="stat-card-value">{riskCount}</div>
          <div className="stat-card-sub">из {data.total_employees} сотрудников</div>
          <div className="stat-card-icon" style={{ background: '#fee2e2', color: '#ef4444' }}>
            <ExclamationCircleOutlined />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Активных команд</div>
          <div className="stat-card-value">1</div>
          <div className="stat-card-sub">{data.total_employees} сотрудников</div>
          <div className="stat-card-icon" style={{ background: '#f0e7ff', color: '#7c3aed' }}>
            <TeamOutlined />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Новых уведомлений</div>
          <div className="stat-card-value">0</div>
          <div className="stat-card-sub">требуют внимания</div>
          <div className="stat-card-icon" style={{ background: '#fef9c3', color: '#ca8a04' }}>
            <ClockCircleOutlined />
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-title">Динамика настроения</div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tickFormatter={formatShortDate} fontSize={12} stroke="#ccc" />
              <YAxis domain={[0, 100]} fontSize={12} stroke="#ccc" />
              <Tooltip
                labelFormatter={(label) => formatShortDate(String(label))}
                formatter={(value) => [value, 'Индекс']}
              />
              <Line type="monotone" dataKey="mood_index" stroke="#7c3aed" strokeWidth={2} dot={{ r: 4, fill: '#7c3aed' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Распределение рисков</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${Math.round((percent ?? 0) * 100)}%`}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
