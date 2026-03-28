import client from './client';
import type { MotivationContent, CreateContentRequest, PaginatedResponse } from '../types';

export async function getContent(params?: {
  type?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<MotivationContent>> {
  const res = await client.get('/content', { params });
  return res.data;
}

export async function createContent(data: CreateContentRequest): Promise<void> {
  await client.post('/content', data);
}

export async function deleteContent(id: string): Promise<void> {
  await client.delete(`/content/${id}`);
}
