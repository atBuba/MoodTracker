import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Table, Row, Col, message } from 'antd';
import type { User, EmployeeState, PaginationMeta } from '../../types';
import { getEmployee, getEmployeeStates } from '../../api/employees';
import MoodBadge from '../../components/employees/MoodBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { formatDate } from '../../utils/formatDate';

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [employee, setEmployee] = useState<User | null>(null);
  const [states, setStates] = useState<EmployeeState[]>([]);
  const [meta, setMeta] = useState<PaginationMeta>({ total: 0, page: 1, per_page: 20 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getEmployee(id),
      getEmployeeStates(id),
    ])
      .then(([emp, statesRes]) => {
        setEmployee(emp);
        setStates(statesRes.data);
        setMeta(statesRes.meta);
      })
      .catch(() => message.error('Ошибка загрузки'))
      .finally(() => setLoading(false));
  }, [id]);

  const fetchStates = (page: number) => {
    if (!id) return;
    getEmployeeStates(id, { page })
      .then((res) => {
        setStates(res.data);
        setMeta(res.meta);
      });
  };

  if (loading || !employee) return <LoadingSpinner />;

  const stateColumns = [
    { title: 'Дата', dataIndex: 'date', key: 'date', render: (d: string) => formatDate(d) },
    {
      title: 'Mood Index',
      dataIndex: 'mood_index',
      key: 'mood_index',
      render: (v: number) => <MoodBadge value={v} />,
    },
    { title: 'Анализ', dataIndex: 'analysis_summary', key: 'analysis_summary', render: (v: string | null) => v ?? '—' },
  ];

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title="Информация о сотруднике">
          <Descriptions column={2}>
            <Descriptions.Item label="Имя">{employee.full_name}</Descriptions.Item>
            <Descriptions.Item label="Email">{employee.email}</Descriptions.Item>
            <Descriptions.Item label="Роль">{employee.role}</Descriptions.Item>
            <Descriptions.Item label="Анализ разрешён">{employee.analysis_allowed ? 'Да' : 'Нет'}</Descriptions.Item>
          </Descriptions>
        </Card>
      </Col>
      <Col span={24}>
        <Card title="История состояний">
          <Table
            dataSource={states}
            columns={stateColumns}
            rowKey="id"
            pagination={{
              current: meta.page,
              pageSize: meta.per_page,
              total: meta.total,
              onChange: fetchStates,
            }}
          />
        </Card>
      </Col>
    </Row>
  );
}
