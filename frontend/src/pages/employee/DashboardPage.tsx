import { useEffect, useState } from 'react';
import { message } from 'antd';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { SmileOutlined, LineChartOutlined } from '@ant-design/icons';
import type { EmployeeDashboard } from '../../types';
import { getEmployeeDashboard } from '../../api/dashboard';
import { displayMood, getMoodColor, getRiskLevel } from '../../utils/moodColor';
import { formatShortDate } from '../../utils/formatDate';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function EmployeeDashboardPage() {
  const [data, setData] = useState<EmployeeDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getEmployeeDashboard()
      .then(setData)
      .catch(() => message.error('Ошибка загрузки'))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return <LoadingSpinner />;

  const moodDisplay = displayMood(data.mood_index);
  const risk = getRiskLevel(data.mood_index);
  const trendData = data.mood_trend_30d.map((p) => ({
    ...p,
    mood_index: displayMood(p.mood_index) ?? 0,
  }));

  return (
    <div>
      <div className="page-header">
        <h1>Мой дашборд</h1>
        <p>Ваше текущее состояние и динамика настроения</p>
      </div>

      <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-card-label">Текущий индекс</div>
          <div className="stat-card-value" style={{ color: getMoodColor(data.mood_index) }}>
            {moodDisplay ?? '—'}
          </div>
          <div className="stat-card-icon" style={{ background: '#f0e7ff', color: '#7c3aed' }}>
            <LineChartOutlined />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Эмоция</div>
          <div className="stat-card-value" style={{ fontSize: 24 }}>
            {data.emotion ?? 'Нет данных'}
          </div>
          <div className="stat-card-icon" style={{ background: '#fef9c3', color: '#ca8a04' }}>
            <SmileOutlined />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Уровень</div>
          <div style={{ marginTop: 8 }}>
            <span className={`risk-badge ${risk.className}`}>{risk.label}</span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title">Динамика настроения (30 дней)</div>
        <ResponsiveContainer width="100%" height={300}>
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

      {data.analysis_summary && (
        <div className="card">
          <div className="card-title">Анализ</div>
          <p style={{ fontSize: 14, color: '#555', lineHeight: 1.6 }}>{data.analysis_summary}</p>
        </div>
      )}
    </div>
  );
}
