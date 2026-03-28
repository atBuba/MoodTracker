import { Card, Statistic } from 'antd';
import { getMoodColor } from '../../utils/moodColor';

interface Props {
  title: string;
  value: number | null | undefined;
  prefix?: React.ReactNode;
}

export default function MoodIndexCard({ title, value, prefix }: Props) {
  return (
    <Card>
      <Statistic
        title={title}
        value={value != null ? value.toFixed(2) : '—'}
        valueStyle={{ color: getMoodColor(value) }}
        prefix={prefix}
      />
    </Card>
  );
}
