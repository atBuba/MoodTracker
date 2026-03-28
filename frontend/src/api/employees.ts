import client from './client';
import type { User, EmployeeState, PaginatedResponse } from '../types';

export async function getEmployees(params?: {
  team_id?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<User>> {
  const res = await client.get('/employees', { params });
  return res.data;
}

export async function getEmployee(id: string): Promise<User> {
  const res = await client.get(`/employees/${id}`);
  return res.data.data;
}

export async function getEmployeeStates(
  id: string,
  params?: { date_from?: string; date_to?: string; page?: number; per_page?: number }
): Promise<PaginatedResponse<EmployeeState>> {
  const res = await client.get(`/employees/${id}/states`, { params });
  return res.data;
}

export async function updateMySettings(analysis_allowed: boolean): Promise<void> {
  await client.patch('/employees/me/settings', { analysis_allowed });
}
