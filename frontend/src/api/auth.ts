import axios from 'axios';
import client from './client';
import type { TokenResponse, User } from '../types';

export async function login(email: string, password: string): Promise<TokenResponse> {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);
  const res = await axios.post<TokenResponse>('/api/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    withCredentials: true,
  });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await client.get('/auth/me');
  // Backend returns UserResponse directly (no {data:...} wrapper)
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout');
}
