'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, AdminUser } from '@/lib/auth';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: Array<'owner' | 'admin' | 'user'>;
}

export default function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);
  const [user, setUser] = useState<AdminUser | null>(null);

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      router.push('/login');
      return;
    }

    setUser(currentUser);
    setIsAuthenticated(true);

    // Check role-based permissions if required
    if (requiredRoles && requiredRoles.length > 0) {
      if (!requiredRoles.includes(currentUser.role)) {
        setHasPermission(false);
        return;
      }
    }

    setHasPermission(true);
  }, [router, requiredRoles]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!hasPermission) {
    return (
      <div className="flex h-screen items-center justify-center p-8">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            You do not have permission to access this page.
            {requiredRoles && requiredRoles.length > 0 && (
              <>
                {' Required role: '}
                {requiredRoles.join(', ')}
              </>
            )}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <>{children}</>;
}
