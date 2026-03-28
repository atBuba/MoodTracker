import { useState } from 'react';
import { Form, Input, message } from 'antd';
import { MailOutlined, LockOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.email, values.password);
      const user = useAuthStore.getState().user;
      if (user?.role === 'employee') {
        navigate('/my-dashboard', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch {
      message.error('Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      minHeight: '100vh', background: '#f8f8fb',
    }}>
      <div style={{
        width: 420, background: '#fff', borderRadius: 16,
        padding: '40px 36px', border: '1px solid #f0f0f0',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 24, marginBottom: 16,
          }}>
            <AppstoreOutlined />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>
            BurnOutDetector
          </h2>
          <p style={{ color: '#999', fontSize: 13 }}>Мониторинг благополучия сотрудников</p>
        </div>

        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="email" rules={[{ required: true, message: 'Введите email' }]}>
            <Input
              prefix={<MailOutlined style={{ color: '#bbb' }} />}
              placeholder="Email"
              size="large"
              style={{ borderRadius: 10 }}
            />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Введите пароль' }]}>
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bbb' }} />}
              placeholder="Пароль"
              size="large"
              style={{ borderRadius: 10 }}
            />
          </Form.Item>
          <Form.Item>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ fontSize: 16, padding: 14, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
}
