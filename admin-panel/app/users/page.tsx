'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Plus, Trash2, Shield } from 'lucide-react';
import { api } from '@/lib/api-client';
import { AdminUser } from '@/lib/auth';

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    display_name: '',
    password: '',
    role: 'user' as 'owner' | 'admin' | 'user',
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError('');
      const users = await api.getAdminUsers();
      setUsers(users);
    } catch (error: any) {
      console.error('Failed to load users:', error);
      setError(error.message || 'Failed to load users');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.createAdminUser(formData);
      setShowCreateForm(false);
      setFormData({ email: '', display_name: '', password: '', role: 'user' });
      await loadUsers();
    } catch (error: any) {
      console.error('Failed to create user:', error);
      setError(error.message || 'Failed to create user');
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to deactivate ${email}?`)) {
      return;
    }

    try {
      setError('');
      await api.deleteAdminUser(userId);
      await loadUsers();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      setError(error.message || 'Failed to delete user');
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      case 'user':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <ProtectedRoute requiredRoles={['owner', 'admin']}>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Admin Users</h1>
                <p className="text-muted-foreground">Manage admin dashboard users and permissions</p>
              </div>
              <Button onClick={() => setShowCreateForm(!showCreateForm)}>
                <Plus className="mr-2 h-4 w-4" />
                New User
              </Button>
            </div>

            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Create Admin User</CardTitle>
                  <CardDescription>Add a new user to the admin dashboard</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="display_name">Display Name</Label>
                      <Input
                        id="display_name"
                        value={formData.display_name}
                        onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                        placeholder="John Doe"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="user@example.com"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password">Password</Label>
                      <Input
                        id="password"
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="Minimum 8 characters"
                        minLength={8}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="role">Role</Label>
                      <select
                        id="role"
                        value={formData.role}
                        onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        required
                      >
                        <option value="user">User (Read-only)</option>
                        <option value="admin">Admin (Manage resources)</option>
                        <option value="owner">Owner (Full access)</option>
                      </select>
                      <p className="text-xs text-muted-foreground">
                        User: Read-only | Admin: Manage resources | Owner: Full access
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">Create User</Button>
                      <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Admin Users</CardTitle>
                <CardDescription>
                  {users.length} user{users.length !== 1 ? 's' : ''} in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground">Loading...</div>
                ) : users.length === 0 ? (
                  <div className="text-center text-muted-foreground">No users found</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Last Login</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.user_id}>
                          <TableCell className="font-medium">{user.display_name}</TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getRoleBadgeColor(user.role)}`}>
                              {user.role === 'owner' && <Shield className="mr-1 h-3 w-3" />}
                              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex rounded-full px-2 py-1 text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {user.last_login
                              ? new Date(user.last_login).toLocaleDateString()
                              : 'Never'}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(user.user_id, user.email)}
                              disabled={!user.is_active}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
