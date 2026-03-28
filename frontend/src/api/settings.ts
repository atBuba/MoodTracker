import client from './client';
import type { ManagerSettings } from '../types';

export async function getSettings(): Promise<ManagerSettings> {
  const res = await client.get('/settings');
  return res.data.data;
}

export async function updateSettings(data: Partial<ManagerSettings>): Promise<void> {
  await client.patch('/settings', data);
}
