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
import { Plus, Trash2, Edit, X } from 'lucide-react';
import { ModelAccessGroup, ModelAlias } from '@/types';
import { api } from '@/lib/api-client';

export default function ModelAccessGroupsPage() {
  const [groups, setGroups] = useState<ModelAccessGroup[]>([]);
  const [models, setModels] = useState<ModelAlias[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingGroup, setEditingGroup] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    group_name: '',
    display_name: '',
    description: '',
    model_aliases: [] as string[],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [groupsData, modelsData] = await Promise.all([
        api.getModelAccessGroups(),
        api.getModelAliases(),
      ]);
      setGroups(groupsData);
      setModels(modelsData);
    } catch (error) {
      console.error('Failed to load data:', error);
      setGroups([]);
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingGroup) {
        // Update existing group
        await api.updateModelAccessGroup(editingGroup, {
          display_name: formData.display_name,
          description: formData.description,
        });
        // Update models separately
        await api.updateModelAccessGroupModels(editingGroup, formData.model_aliases);
      } else {
        // Create new group
        await api.createModelAccessGroup(formData);
      }

      setShowCreateForm(false);
      setEditingGroup(null);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error('Failed to save model access group:', error);
      alert(`Failed to save group: ${error.message}`);
    }
  };

  const handleEdit = (group: ModelAccessGroup) => {
    setFormData({
      group_name: group.group_name,
      display_name: group.display_name,
      description: group.description || '',
      model_aliases: group.model_aliases.map((m) => m.model_alias),
    });
    setEditingGroup(group.group_name);
    setShowCreateForm(true);
  };

  const handleDelete = async (groupName: string) => {
    const group = groups.find(g => g.group_name === groupName);
    const teamsCount = group?.teams_using?.length || 0;

    if (teamsCount > 0) {
      if (!confirm(
        `Warning: ${teamsCount} team(s) are using this group. Deleting it will remove model access for these teams. Are you sure?`
      )) {
        return;
      }
    } else {
      if (!confirm(`Are you sure you want to delete group "${groupName}"?`)) {
        return;
      }
    }

    try {
      await api.deleteModelAccessGroup(groupName);
      loadData();
    } catch (error: any) {
      console.error('Failed to delete model access group:', error);
      alert(`Failed to delete group: ${error.message}`);
    }
  };

  const toggleModelAlias = (alias: string) => {
    if (formData.model_aliases.includes(alias)) {
      setFormData({
        ...formData,
        model_aliases: formData.model_aliases.filter((a) => a !== alias),
      });
    } else {
      setFormData({
        ...formData,
        model_aliases: [...formData.model_aliases, alias],
      });
    }
  };

  const resetForm = () => {
    setFormData({
      group_name: '',
      display_name: '',
      description: '',
      model_aliases: [],
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
                <h1 className="text-3xl font-bold">Model Access Groups</h1>
                <p className="text-muted-foreground">
                  Create groups of model aliases and assign them to teams
                </p>
              </div>
              <Button
                onClick={() => {
                  resetForm();
                  setEditingGroup(null);
                  setShowCreateForm(!showCreateForm);
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Access Group
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>
                    {editingGroup ? 'Edit Access Group' : 'Create Access Group'}
                  </CardTitle>
                  <CardDescription>
                    {editingGroup
                      ? 'Update the access group details and model assignments'
                      : 'Create a collection of model aliases for team access control'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="group_name">Group Name *</Label>
                        <Input
                          id="group_name"
                          placeholder="e.g., basic-chat"
                          value={formData.group_name}
                          onChange={(e) =>
                            setFormData({ ...formData, group_name: e.target.value })
                          }
                          required
                          disabled={!!editingGroup}
                        />
                        <p className="text-xs text-muted-foreground">
                          Unique identifier (cannot be changed after creation)
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="display_name">Display Name *</Label>
                        <Input
                          id="display_name"
                          placeholder="e.g., Basic Chat Models"
                          value={formData.display_name}
                          onChange={(e) =>
                            setFormData({ ...formData, display_name: e.target.value })
                          }
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        placeholder="Optional description"
                        value={formData.description}
                        onChange={(e) =>
                          setFormData({ ...formData, description: e.target.value })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Model Aliases</Label>
                      {models.length > 0 ? (
                        <div className="border rounded-md p-4 space-y-2 max-h-64 overflow-y-auto">
                          {models.map((model) => (
                            <div
                              key={model.model_alias}
                              className="flex items-center space-x-2 p-2 hover:bg-accent rounded cursor-pointer"
                              onClick={() => toggleModelAlias(model.model_alias)}
                            >
                              <input
                                type="checkbox"
                                checked={formData.model_aliases.includes(model.model_alias)}
                                onChange={() => toggleModelAlias(model.model_alias)}
                                className="h-4 w-4 rounded border-primary text-primary"
                              />
                              <div className="flex-1">
                                <div className="font-medium">{model.display_name}</div>
                                <div className="text-xs text-muted-foreground">
                                  {model.model_alias} → {model.actual_model}
                                </div>
                              </div>
                              <Badge className={
                                model.provider === 'openai' ? 'bg-green-500' :
                                model.provider === 'anthropic' ? 'bg-orange-500' :
                                model.provider === 'google' ? 'bg-blue-500' :
                                'bg-gray-500'
                              }>
                                {model.provider}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No model aliases available. Create model aliases first to add them to groups.
                        </p>
                      )}
                      {formData.model_aliases.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {formData.model_aliases.map((alias) => {
                            const model = models.find(m => m.model_alias === alias);
                            return (
                              <Badge
                                key={alias}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => toggleModelAlias(alias)}
                              >
                                {model?.display_name || alias} <X className="h-3 w-3 ml-1" />
                              </Badge>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">
                        {editingGroup ? 'Update Group' : 'Create Group'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setShowCreateForm(false);
                          setEditingGroup(null);
                          resetForm();
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Access Groups</CardTitle>
                <CardDescription>
                  All model access groups in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : groups.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    No access groups yet. Create one to get started.
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Group Name</TableHead>
                        <TableHead>Display Name</TableHead>
                        <TableHead>Model Aliases</TableHead>
                        <TableHead>Teams Using</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {groups.map((group) => (
                        <TableRow key={group.group_name}>
                          <TableCell className="font-mono font-semibold">
                            {group.group_name}
                          </TableCell>
                          <TableCell>{group.display_name}</TableCell>
                          <TableCell>
                            {group.model_aliases.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {group.model_aliases.map((model) => (
                                  <Badge
                                    key={model.model_alias}
                                    variant="outline"
                                    className="text-xs"
                                    title={`${model.display_name} → ${model.actual_model}`}
                                  >
                                    {model.model_alias}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">No models</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {group.teams_using && group.teams_using.length > 0 ? (
                              <Badge variant="secondary">{group.teams_using.length} teams</Badge>
                            ) : (
                              <span className="text-muted-foreground text-sm">0 teams</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant={group.status === 'active' ? 'default' : 'secondary'}>
                              {group.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1 justify-end">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(group)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(group.group_name)}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
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
