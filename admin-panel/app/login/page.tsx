'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const [adminKey, setAdminKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const user = await login(adminKey);
      if (user) {
        router.push('/');
      } else {
        setError('Invalid admin key. Please check your MASTER_KEY.');
      }
    } catch (err) {
      setError('Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Admin Login</CardTitle>
          <CardDescription>Enter your admin master key to access the SaaS API Admin Panel</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="adminKey">Admin Master Key</Label>
              <Input
                id="adminKey"
                type="password"
                placeholder="sk-admin-..."
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                required
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                This is the MASTER_KEY value from your .env file
              </p>
            </div>

            {error && (
              <div className="text-sm text-destructive">{error}</div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          {process.env.NODE_ENV === 'development' && (
            <div className="mt-4 space-y-2 text-sm text-muted-foreground">
              <p className="font-medium">Development Default:</p>
              <p className="font-mono text-xs break-all">sk-admin-local-dev-change-in-production</p>
              <p className="text-xs">Change this in production! See SECURITY.md</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
