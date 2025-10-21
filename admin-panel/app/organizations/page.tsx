'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Activity } from 'lucide-react';
import { Organization } from '@/types';
import { api } from '@/lib/api-client';
import { useRouter } from 'next/navigation';

export default function OrganizationsPage() {
  const router = useRouter();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    organization_id: '',
    name: '',
    create_default_team: true,
    default_team_name: '',
    default_team_access_groups: [] as string[],
    default_team_credits: 1000,
  });
  const [accessGroupInput, setAccessGroupInput] = useState('');

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const data = await api.getOrganizations();
      setOrganizations(data);
    } catch (error) {
      console.error('Failed to load organizations:', error);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createOrganization(formData);
      setShowCreateForm(false);
      setFormData({
        organization_id: '',
        name: '',
        create_default_team: true,
        default_team_name: '',
        default_team_access_groups: [],
        default_team_credits: 1000,
      });
      setAccessGroupInput('');
      loadOrganizations();
    } catch (error: any) {
      console.error('Failed to create organization:', error);
      alert(`Failed to create organization: ${error.message}`);
    }
  };

  const addAccessGroup = () => {
    if (accessGroupInput && !formData.default_team_access_groups.includes(accessGroupInput)) {
      setFormData({
        ...formData,
        default_team_access_groups: [...formData.default_team_access_groups, accessGroupInput],
      });
      setAccessGroupInput('');
    }
  };

  const removeAccessGroup = (group: string) => {
    setFormData({
      ...formData,
      default_team_access_groups: formData.default_team_access_groups.filter((g) => g !== group),
    });
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Organizations</h1>
                <p className="text-muted-foreground">Manage your organizations</p>
              </div>
              <Button onClick={() => setShowCreateForm(!showCreateForm)}>
                <Plus className="mr-2 h-4 w-4" />
                New Organization
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Create Organization</CardTitle>
                  <CardDescription>Add a new organization to the system</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="organization_id">Organization ID *</Label>
                        <Input
                          id="organization_id"
                          placeholder="e.g., acme-corp"
                          value={formData.organization_id}
                          onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                          required
                        />
                        <p className="text-xs text-muted-foreground">
                          Unique identifier for this organization
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="name">Organization Name *</Label>
                        <Input
                          id="name"
                          placeholder="e.g., Acme Corporation"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="create_default_team"
                          checked={formData.create_default_team}
                          onCheckedChange={(checked) =>
                            setFormData({ ...formData, create_default_team: checked as boolean })
                          }
                        />
                        <Label htmlFor="create_default_team" className="font-semibold">
                          Create Default Team
                        </Label>
                      </div>

                      {formData.create_default_team && (
                        <div className="space-y-4 pl-6">
                          <div className="space-y-2">
                            <Label htmlFor="default_team_name">Default Team Name</Label>
                            <Input
                              id="default_team_name"
                              placeholder="Leave empty to use organization name"
                              value={formData.default_team_name}
                              onChange={(e) =>
                                setFormData({ ...formData, default_team_name: e.target.value })
                              }
                            />
                          </div>

                          <div className="space-y-2">
                            <Label>Model Access Groups</Label>
                            <div className="flex gap-2">
                              <Input
                                placeholder="Enter access group name (e.g., basic-chat)"
                                value={accessGroupInput}
                                onChange={(e) => setAccessGroupInput(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') {
                                    e.preventDefault();
                                    addAccessGroup();
                                  }
                                }}
                              />
                              <Button type="button" variant="outline" onClick={addAccessGroup}>
                                Add
                              </Button>
                            </div>
                            {formData.default_team_access_groups.length > 0 ? (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {formData.default_team_access_groups.map((group) => (
                                  <Badge
                                    key={group}
                                    variant="secondary"
                                    className="cursor-pointer"
                                    onClick={() => removeAccessGroup(group)}
                                  >
                                    {group} ×
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground mt-2">
                                No access groups added. Add groups to grant model access to the default team.
                              </p>
                            )}
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="default_team_credits">Initial Credits</Label>
                            <Input
                              id="default_team_credits"
                              type="number"
                              value={formData.default_team_credits}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  default_team_credits: Number(e.target.value),
                                })
                              }
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">Create Organization</Button>
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
                <CardTitle>Organizations List</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground">Loading...</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {organizations.map((org) => (
                        <TableRow key={org.organization_id}>
                          <TableCell className="font-mono text-sm">{org.organization_id}</TableCell>
                          <TableCell className="font-medium">{org.name}</TableCell>
                          <TableCell>
                            <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700">
                              {org.status}
                            </span>
                          </TableCell>
                          <TableCell>{new Date(org.created_at).toLocaleDateString()}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => router.push(`/jobs/organizations/${org.organization_id}`)}
                              title="View organization analytics"
                            >
                              <Activity className="h-4 w-4 text-blue-500" />
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
