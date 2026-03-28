import { create } from 'zustand';
import type { User } from '../types';
import * as authApi from '../api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,

  login: async (email, password) => {
    const { access_token } = await authApi.login(email, password);
    localStorage.setItem('access_token', access_token);
    const user = await authApi.getMe();
    set({ user, isAuthenticated: true });
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem('access_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  loadUser: async () => {
    set({ loading: true });
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true, loading: false });
    } catch {
      localStorage.removeItem('access_token');
      set({ user: null, isAuthenticated: false, loading: false });
    }
  },
}));
