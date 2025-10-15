'use client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

export interface AdminUser {
  user_id: string;
  email: string;
  display_name: string;
  role: 'owner' | 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AdminUser;
}

/**
 * Check if setup is required (no admin users exist)
 */
export async function needsSetup(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/admin-users/setup/status`);
    if (response.ok) {
      const data = await response.json();
      return data.needs_setup === true;
    }
    return false;
  } catch (error) {
    console.error('Failed to check setup status:', error);
    return false;
  }
}

/**
 * Create the first owner user (setup)
 */
export async function setupOwner(
  email: string,
  password: string,
  displayName: string
): Promise<LoginResponse | null> {
  try {
    const response = await fetch(`${API_URL}/api/admin-users/setup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      // Store JWT token and user info
      localStorage.setItem('jwtToken', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    }

    return null;
  } catch (error) {
    console.error('Setup failed:', error);
    return null;
  }
}

/**
 * Login with email and password (JWT authentication)
 */
export async function loginWithPassword(
  email: string,
  password: string
): Promise<LoginResponse | null> {
  try {
    const response = await fetch(`${API_URL}/api/admin-users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      // Store JWT token and user info
      localStorage.setItem('jwtToken', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    }

    return null;
  } catch (error) {
    console.error('Login failed:', error);
    return null;
  }
}

/**
 * Logout (revoke JWT token)
 */
export async function logout(): Promise<void> {
  try {
    const token = getJWTToken();
    if (token) {
      await fetch(`${API_URL}/api/admin-users/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    // Always clear local storage
    localStorage.removeItem('user');
    localStorage.removeItem('jwtToken');
    // Keep adminKey for backward compatibility (legacy auth)
    localStorage.removeItem('adminKey');
  }
}

/**
 * Get current user from localStorage
 */
export function getCurrentUser(): AdminUser | null {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

/**
 * Check if current user is an owner
 */
export function isOwner(): boolean {
  const user = getCurrentUser();
  return user?.role === 'owner';
}

/**
 * Check if current user is an admin or owner
 */
export function isAdmin(): boolean {
  const user = getCurrentUser();
  return user?.role === 'admin' || user?.role === 'owner';
}

/**
 * Get JWT token from localStorage
 */
export function getJWTToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('jwtToken');
}

/**
 * Legacy: Get admin key from localStorage (for backward compatibility)
 * @deprecated Use getJWTToken() instead
 */
export function getAdminKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('adminKey');
}
