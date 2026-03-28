// Mood index is 0-1 from backend, displayed as 0-100
export function displayMood(index: number | null | undefined): number | null {
  if (index == null) return null;
  return Math.round(index * 100);
}

export function getMoodColor(index: number | null | undefined): string {
  if (index == null) return '#d9d9d9';
  const v = index <= 1 ? index * 100 : index;
  if (v < 30) return '#ef4444';
  if (v < 50) return '#ea580c';
  if (v < 70) return '#f59e0b';
  return '#22c55e';
}

export function getRiskLevel(index: number | null | undefined): { label: string; className: string } {
  if (index == null) return { label: 'Нет данных', className: '' };
  const v = index <= 1 ? index * 100 : index;
  if (v < 30) return { label: 'Критический', className: 'critical' };
  if (v < 50) return { label: 'Высокий', className: 'high' };
  if (v < 70) return { label: 'Средний', className: 'medium' };
  return { label: 'Низкий', className: 'low' };
}

export function getMoodLabel(index: number | null | undefined): string {
  return getRiskLevel(index).label;
}

export function getTrendIcon(trend: string | null | undefined): { icon: string; color: string } {
  if (trend === 'declining') return { icon: '↘', color: '#ef4444' };
  if (trend === 'improving') return { icon: '↗', color: '#22c55e' };
  return { icon: '—', color: '#999' };
}
