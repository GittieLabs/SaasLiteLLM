'use client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

/**
 * Login with MASTER_KEY (Admin API Key)
 *
 * This validates the admin key by making a test API call.
 * If successful, stores the key in localStorage for future requests.
 *
 * @param adminKey - The MASTER_KEY from environment (e.g., sk-admin-...)
 * @returns User object if valid, null if invalid
 */
export async function login(adminKey: string): Promise<{id: string, username: string, role: 'owner'} | null> {
  try {
    // Test the admin key by making an API call
    // We'll use a simple endpoint that requires admin auth
    const response = await fetch(`${API_URL}/api/model-groups`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Key': adminKey,
      },
    });

    if (response.ok) {
      // Valid admin key - store it
      localStorage.setItem('adminKey', adminKey);

      // Create user object
      const user = {
        id: "admin",
        username: "Administrator",
        role: "owner" as const
      };

      localStorage.setItem('user', JSON.stringify(user));
      return user;
    }

    return null;
  } catch (error) {
    console.error('Login failed:', error);
    return null;
  }
}

export function logout() {
  localStorage.removeItem('user');
  localStorage.removeItem('adminKey');
}

export function getCurrentUser() {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

export function isOwner() {
  const user = getCurrentUser();
  return user?.role === 'owner';
}

export function getAdminKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('adminKey');
}
