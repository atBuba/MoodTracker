import { create } from 'zustand';
import { getUnreadCount } from '../api/notifications';

interface NotificationState {
  unreadCount: number;
  fetchUnreadCount: () => Promise<void>;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,

  fetchUnreadCount: async () => {
    try {
      const count = await getUnreadCount();
      set({ unreadCount: count });
    } catch {
      // ignore errors silently
    }
  },
}));
