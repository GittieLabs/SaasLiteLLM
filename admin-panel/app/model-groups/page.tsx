'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus } from 'lucide-react';
import { ModelGroup } from '@/types';
import { api } from '@/lib/api-client';

export default function ModelGroupsPage() {
  const [modelGroups, setModelGroups] = useState<ModelGroup[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    group_name: '',
    display_name: '',
    description: '',
  });

  useEffect(() => {
    loadModelGroups();
  }, []);

  const loadModelGroups = async () => {
    try {
      setLoading(true);
      // Mock data for demo - replace with actual API call
      const mockGroups: ModelGroup[] = [
        {
          model_group_id: 'mg_1',
          group_name: 'gpt-4-group',
          display_name: 'GPT-4 Models',
          description: 'High-performance GPT-4 models',
          status: 'active',
          models: [
            { model_name: 'gpt-4', priority: 1 },
            { model_name: 'gpt-4-turbo', priority: 2 },
          ],
        },
        {
          model_group_id: 'mg_2',
          group_name: 'claude-3-group',
          display_name: 'Claude 3 Models',
          description: 'Anthropic Claude 3 family',
          status: 'active',
          models: [
            { model_name: 'claude-3-opus', priority: 1 },
            { model_name: 'claude-3-sonnet', priority: 2 },
          ],
        },
        {
          model_group_id: 'mg_3',
          group_name: 'budget-group',
          display_name: 'Budget Models',
          description: 'Cost-effective models',
          status: 'active',
          models: [
            { model_name: 'gpt-3.5-turbo', priority: 1 },
            { model_name: 'claude-instant', priority: 2 },
          ],
        },
      ];
      setModelGroups(mockGroups);
    } catch (error) {
      console.error('Failed to load model groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createModelGroup(formData);
      setShowCreateForm(false);
      setFormData({ group_name: '', display_name: '', description: '' });
      loadModelGroups();
    } catch (error) {
      console.error('Failed to create model group:', error);
    }
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Model Groups</h1>
                <p className="text-muted-foreground">Configure model routing groups</p>
              </div>
              <Button onClick={() => setShowCreateForm(!showCreateForm)}>
                <Plus className="mr-2 h-4 w-4" />
                New Model Group
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Create Model Group</CardTitle>
                  <CardDescription>Add a new model group configuration</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="group_name">Group Name (ID)</Label>
                      <Input
                        id="group_name"
                        value={formData.group_name}
                        onChange={(e) => setFormData({ ...formData, group_name: e.target.value })}
                        placeholder="e.g., gpt-4-group"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="display_name">Display Name</Label>
                      <Input
                        id="display_name"
                        value={formData.display_name}
                        onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                        placeholder="e.g., GPT-4 Models"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Optional description"
                      />
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">Create</Button>
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
                <CardTitle>Model Groups List</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground">Loading...</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Display Name</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Models</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {modelGroups.map((group) => (
                        <TableRow key={group.model_group_id}>
                          <TableCell className="font-mono text-sm">{group.group_name}</TableCell>
                          <TableCell className="font-medium">{group.display_name}</TableCell>
                          <TableCell className="text-muted-foreground">{group.description}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {group.models.map((model, idx) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700"
                                >
                                  {model.model_name}
                                </span>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700">
                              {group.status}
                            </span>
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
