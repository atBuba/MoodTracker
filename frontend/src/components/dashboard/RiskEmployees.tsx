import { Card, Table } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { RiskEmployee } from '../../types';
import MoodBadge from '../employees/MoodBadge';

interface Props {
  data: RiskEmployee[];
}

export default function RiskEmployees({ data }: Props) {
  const navigate = useNavigate();

  const columns = [
    { title: 'Сотрудник', dataIndex: 'full_name', key: 'full_name' },
    {
      title: 'Mood Index',
      dataIndex: 'mood_index',
      key: 'mood_index',
      render: (v: number) => <MoodBadge value={v} />,
    },
    { title: 'Тренд', dataIndex: 'trend', key: 'trend', render: (v: string | null) => v ?? '—' },
  ];

  return (
    <Card title="Сотрудники в зоне риска">
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        pagination={false}
        size="small"
        onRow={(record) => ({
          onClick: () => navigate(`/employees/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </Card>
  );
}
