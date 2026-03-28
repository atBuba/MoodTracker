import { Card } from 'antd';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';
import type { MoodTrendPoint } from '../../types';
import { formatShortDate } from '../../utils/formatDate';

interface Props {
  data: MoodTrendPoint[];
  threshold?: number;
}

export default function MoodTrendChart({ data, threshold }: Props) {
  return (
    <Card title="Динамика настроения (30 дней)">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tickFormatter={formatShortDate} />
          <YAxis domain={[0, 1]} />
          <Tooltip
            labelFormatter={(label) => formatShortDate(String(label))}
            formatter={(value) => [Number(value).toFixed(2), 'Mood Index']}
          />
          {threshold != null && (
            <ReferenceLine y={threshold} stroke="#faad14" strokeDasharray="5 5" label="Порог" />
          )}
          <Line type="monotone" dataKey="mood_index" stroke="#1890ff" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
