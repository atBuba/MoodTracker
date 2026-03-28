import { Tag } from 'antd';
import { getMoodColor, getMoodLabel } from '../../utils/moodColor';

interface Props {
  value: number | null | undefined;
}

export default function MoodBadge({ value }: Props) {
  return (
    <Tag color={getMoodColor(value)}>
      {value != null ? `${value.toFixed(2)} — ${getMoodLabel(value)}` : getMoodLabel(value)}
    </Tag>
  );
}
