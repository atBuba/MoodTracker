import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import LoadingSpinner from './LoadingSpinner';

interface Props {
  children: React.ReactNode;
  roles?: string[];
}

export default function ProtectedRoute({ children, roles }: Props) {
  const { user, isAuthenticated, loading } = useAuthStore();

  if (loading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!user) return <LoadingSpinner />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" replace />;

  return <>{children}</>;
}
