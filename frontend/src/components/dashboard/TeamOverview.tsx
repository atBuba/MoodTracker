import { Card, Statistic, Col, Row } from 'antd';
import { TeamOutlined, SmileOutlined } from '@ant-design/icons';

interface Props {
  totalEmployees: number;
  avgMoodIndex: number;
}

export default function TeamOverview({ totalEmployees, avgMoodIndex }: Props) {
  return (
    <Row gutter={16}>
      <Col span={12}>
        <Card>
          <Statistic title="Всего сотрудников" value={totalEmployees} prefix={<TeamOutlined />} />
        </Card>
      </Col>
      <Col span={12}>
        <Card>
          <Statistic
            title="Средний Mood Index"
            value={avgMoodIndex.toFixed(2)}
            prefix={<SmileOutlined />}
          />
        </Card>
      </Col>
    </Row>
  );
}
