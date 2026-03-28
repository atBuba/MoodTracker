import client from './client';
import type { ManagerDashboard, EmployeeDashboard } from '../types';

export async function getManagerDashboard(): Promise<ManagerDashboard> {
  const res = await client.get('/dashboard/manager');
  return res.data.data;
}

export async function getEmployeeDashboard(): Promise<EmployeeDashboard> {
  const res = await client.get('/dashboard/employee');
  return res.data.data;
}
