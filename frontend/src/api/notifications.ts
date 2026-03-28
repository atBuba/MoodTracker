import client from './client';
import type { Notification, PaginatedResponse } from '../types';

export async function getNotifications(params?: {
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<Notification>> {
  const res = await client.get('/notifications', { params });
  return res.data;
}

export async function markAsRead(id: string): Promise<void> {
  await client.patch(`/notifications/${id}/read`);
}

export async function getUnreadCount(): Promise<number> {
  const res = await client.get('/notifications/unread-count');
  // Backend wraps in success_response: {data: {unread_count: N}}
  return res.data.data.unread_count;
}
