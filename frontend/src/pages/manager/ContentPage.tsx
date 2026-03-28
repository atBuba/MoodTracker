import { useEffect, useState } from 'react';
import { Input, Modal, Form, Select, message } from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { MotivationContent, PaginationMeta } from '../../types';
import { getContent, createContent, deleteContent } from '../../api/content';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const typeConfig: Record<string, { label: string; className: string; icon: string }> = {
  quote: { label: 'Цитата', className: 'quote', icon: '💬' },
  suggestion: { label: 'Предложение', className: 'suggestion', icon: '💡' },
  meme: { label: 'Мем', className: 'meme', icon: '🖼' },
};

const typeOptions = [
  { value: 'quote', label: 'Цитата' },
  { value: 'suggestion', label: 'Предложение' },
  { value: 'meme', label: 'Мем' },
];

export default function ContentPage() {
  const [items, setItems] = useState<MotivationContent[]>([]);
  const [meta, setMeta] = useState<PaginationMeta>({ total: 0, page: 1, per_page: 20 });
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [form] = Form.useForm();

  const fetchData = (page = 1) => {
    setLoading(true);
    getContent({ page, per_page: 50 })
      .then((res) => { setItems(res.data); setMeta(res.meta); })
      .catch(() => message.error('Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    const values = await form.validateFields();
    const tags = values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : [];
    await createContent({ ...values, tags });
    message.success('Контент добавлен');
    setModalOpen(false);
    form.resetFields();
    fetchData();
  };

  const handleDelete = async (id: string) => {
    await deleteContent(id);
    message.success('Удалено');
    fetchData();
  };

  if (loading) return <LoadingSpinner />;

  const filtered = items.filter((i) =>
    i.content.toLowerCase().includes(search.toLowerCase()) ||
    i.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
  );

  const memeCount = items.filter((i) => i.type === 'meme').length;
  const quoteCount = items.filter((i) => i.type === 'quote').length;
  const suggestionCount = items.filter((i) => i.type === 'suggestion').length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h1>Управление контентом</h1>
          <p>База мемов, цитат и предложений для поддержки сотрудников</p>
        </div>
        <button
          className="btn-primary"
          style={{ width: 'auto', padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 8 }}
          onClick={() => setModalOpen(true)}
        >
          <PlusOutlined /> Добавить контент
        </button>
      </div>

      <div className="stat-cards">
        <div className="stat-card active">
          <div className="stat-card-label">Всего</div>
          <div className="stat-card-value">{meta.total}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #ef4444' }}>
          <div className="stat-card-label" style={{ color: '#ef4444' }}>Мемы</div>
          <div className="stat-card-value" style={{ color: '#ef4444' }}>{memeCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Цитаты</div>
          <div className="stat-card-value">{quoteCount}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #22c55e' }}>
          <div className="stat-card-label" style={{ color: '#22c55e' }}>Предложения</div>
          <div className="stat-card-value" style={{ color: '#22c55e' }}>{suggestionCount}</div>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder="Поиск по содержанию или тегам..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ borderRadius: 10, height: 44 }}
        />
      </div>

      <div className="content-grid">
        {filtered.map((item) => {
          const cfg = typeConfig[item.type] ?? typeConfig.quote;
          return (
            <div className="content-card" key={item.id}>
              <span className={`content-type ${cfg.className}`}>
                {cfg.icon} {cfg.label}
              </span>
              <button className="delete-btn" onClick={() => handleDelete(item.id)}>
                <DeleteOutlined />
              </button>
              <div className="content-text">{item.content}</div>
              <div className="content-tags">
                {item.tags.map((tag) => (
                  <span className="content-tag" key={tag}>#{tag}</span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="card" style={{ marginTop: 20, background: '#faf8ff' }}>
        <div style={{ fontWeight: 600, fontSize: 15, color: '#7c3aed', marginBottom: 4 }}>
          Автоматическая отправка контента
        </div>
        <div style={{ fontSize: 13, color: '#888' }}>
          Система автоматически выбирает подходящий контент из этой базы и отправляет сотрудникам
          при падении их индекса настроения. Контент подбирается на основе тегов и типа ситуации.
        </div>
      </div>

      <Modal
        title="Добавить контент"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="Добавить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="type" label="Тип" rules={[{ required: true }]}>
            <Select options={typeOptions} />
          </Form.Item>
          <Form.Item name="content" label="Контент" rules={[{ required: true }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="tags" label="Теги (через запятую)">
            <Input placeholder="мотивация, успех" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
