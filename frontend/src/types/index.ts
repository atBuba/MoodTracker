export interface User {
  id: string;
  full_name: string;
  email: string;
  role: 'employee' | 'manager' | 'admin';
  team_id: string | null;
  analysis_allowed: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Employee extends User {
  latest_mood_index?: number | null;
  latest_emotion?: string | null;
}

export interface EmployeeState {
  id: string;
  date: string;
  mood_index: number;
  analysis_summary: string | null;
}

export interface MoodTrendPoint {
  date: string;
  mood_index: number;
}

export interface RiskEmployee {
  id: string;
  full_name: string;
  mood_index: number;
  trend: string | null;
}

export interface ManagerDashboard {
  total_employees: number;
  avg_mood_index: number;
  at_risk_employees: RiskEmployee[];
  mood_trend_30d: MoodTrendPoint[];
}

export interface EmployeeDashboard {
  mood_index: number | null;
  emotion: string | null;
  analysis_summary: string | null;
  mood_trend_30d: MoodTrendPoint[];
}

export interface Notification {
  id: string;
  type: 'report' | 'alert' | 'motivation_sent';
  title: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface ManagerSettings {
  threshold_value: number;
  notification_period: 'immediate' | 'daily' | 'weekly';
  auto_motivation_enabled: boolean;
}

export interface MotivationContent {
  id: string;
  type: 'meme' | 'quote' | 'suggestion';
  content: string;
  tags: string[];
  created_at: string;
}

export interface CreateContentRequest {
  type: 'meme' | 'quote' | 'suggestion';
  content: string;
  tags?: string[];
}

export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface ApiResponse<T> {
  data: T;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
