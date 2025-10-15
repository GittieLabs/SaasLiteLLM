'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { needsSetup, setupOwner, loginWithPassword } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function LoginPage() {
  const router = useRouter();
  const [isSetupMode, setIsSetupMode] = useState(false);
  const [isCheckingSetup, setIsCheckingSetup] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Login form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Setup form state (additional field)
  const [displayName, setDisplayName] = useState('');

  // Check if setup is needed on mount
  useEffect(() => {
    const checkSetup = async () => {
      setIsCheckingSetup(true);
      const setupRequired = await needsSetup();
      setIsSetupMode(setupRequired);
      setIsCheckingSetup(false);
    };
    checkSetup();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isSetupMode) {
        // Setup mode - create first owner
        const result = await setupOwner(email, password, displayName);
        if (result) {
          router.push('/');
        } else {
          setError('Setup failed. Please try again.');
        }
      } else {
        // Login mode - authenticate with email/password
        const result = await loginWithPassword(email, password);
        if (result) {
          router.push('/');
        } else {
          setError('Invalid email or password.');
        }
      }
    } catch (err) {
      setError('Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isCheckingSetup) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Loading...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            {isSetupMode ? 'Admin Setup' : 'Admin Login'}
          </CardTitle>
          <CardDescription>
            {isSetupMode
              ? 'Create your admin account to get started'
              : 'Sign in to access the SaaS API Admin Panel'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSetupMode && (
            <Alert className="mb-4">
              <AlertDescription>
                This is the first-time setup. You will be created as the owner with full access.
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSetupMode && (
              <div className="space-y-2">
                <Label htmlFor="displayName">Display Name</Label>
                <Input
                  id="displayName"
                  type="text"
                  placeholder="John Doe"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder={isSetupMode ? 'Create a strong password' : 'Enter your password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                minLength={8}
              />
              {isSetupMode && (
                <p className="text-xs text-muted-foreground">
                  Password must be at least 8 characters
                </p>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading
                ? (isSetupMode ? 'Setting up...' : 'Signing in...')
                : (isSetupMode ? 'Create Admin Account' : 'Sign In')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
