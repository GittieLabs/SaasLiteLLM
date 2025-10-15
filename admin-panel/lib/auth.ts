'use client';

const USERS = [
  { id: "1", username: "admin", password: "admin123", role: "owner" as const },
  { id: "2", username: "user", password: "user123", role: "user" as const },
];

export function login(username: string, password: string) {
  const user = USERS.find(u => u.username === username && u.password === password);
  if (user) {
    const { password: _, ...userWithoutPassword } = user;
    localStorage.setItem('user', JSON.stringify(userWithoutPassword));
    return userWithoutPassword;
  }
  return null;
}

export function logout() {
  localStorage.removeItem('user');
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
