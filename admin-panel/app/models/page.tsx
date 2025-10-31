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
import { ModelAlias, ModelAccessGroup, Organization } from '@/types';
import { api } from '@/lib/api-client';
import { PROVIDERS, getModelsForProvider, getModel } from '@/lib/provider-models';

interface ProviderCredential {
  credential_id: string;
  organization_id: string;
  provider: string;
  credential_name: string;
  is_active: boolean;
}

export default function ModelsPage() {
  const [models, setModels] = useState<ModelAlias[]>([]);
  const [accessGroups, setAccessGroups] = useState<ModelAccessGroup[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingModel, setEditingModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    model_alias: '',
    display_name: '',
    provider: 'openai',
    actual_model: '',
    description: '',
    pricing_input: '',
    pricing_output: '',
    credential_name: '',
    access_groups: [] as string[],
    organization_id: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [modelsData, groupsData, orgsData] = await Promise.all([
        api.getModelAliases(),
        api.getModelAccessGroups(),
        api.getOrganizations(),
      ]);
      setModels(modelsData);
      setAccessGroups(groupsData);
      setOrganizations(orgsData);

      // Load credentials for first org if available
      if (orgsData.length > 0 && !formData.organization_id) {
        const firstOrg = orgsData[0].organization_id;
        setFormData(prev => ({ ...prev, organization_id: firstOrg }));
        await loadCredentials(firstOrg);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      setModels([]);
      setAccessGroups([]);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCredentials = async (organizationId: string) => {
    try {
      const credsData = await api.getProviderCredentials(organizationId);
      setCredentials(credsData);
    } catch (error) {
      console.error('Failed to load credentials:', error);
      setCredentials([]);
    }
  };

  const handleProviderChange = (provider: string) => {
    setFormData({
      ...formData,
      provider,
      actual_model: '', // Reset model when provider changes
      pricing_input: '',
      pricing_output: '',
    });
  };

  const handleModelChange = (modelValue: string) => {
    const modelInfo = getModel(formData.provider, modelValue);
    setFormData({
      ...formData,
      actual_model: modelValue,
      display_name: modelInfo?.label || modelValue,
      pricing_input: modelInfo?.defaultInputPrice?.toString() || '',
      pricing_output: modelInfo?.defaultOutputPrice?.toString() || '',
      description: modelInfo?.description || '',
    });
  };

  const handleOrganizationChange = async (organizationId: string) => {
    setFormData({ ...formData, organization_id: organizationId });
    await loadCredentials(organizationId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        pricing_input: formData.pricing_input ? parseFloat(formData.pricing_input) : undefined,
        pricing_output: formData.pricing_output ? parseFloat(formData.pricing_output) : undefined,
      };

      if (editingModel) {
        await api.updateModelAlias(editingModel, payload);
      } else {
        await api.createModelAlias(payload);
      }

      setShowCreateForm(false);
      setEditingModel(null);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error('Failed to save model alias:', error);
      alert(`Failed to save model: ${error.message}`);
    }
  };

  const handleEdit = (model: ModelAlias) => {
    setFormData({
      model_alias: model.model_alias,
      display_name: model.display_name,
      provider: model.provider,
      actual_model: model.actual_model,
      description: model.description || '',
      pricing_input: model.pricing_input?.toString() || '',
      pricing_output: model.pricing_output?.toString() || '',
      credential_name: '',
      access_groups: model.access_groups || [],
    });
    setEditingModel(model.model_alias);
    setShowCreateForm(true);
  };

  const handleDelete = async (alias: string) => {
    if (!confirm(`Are you sure you want to delete model alias "${alias}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.deleteModelAlias(alias);
      loadData();
    } catch (error: any) {
      console.error('Failed to delete model alias:', error);
      alert(`Failed to delete model: ${error.message}`);
    }
  };

  const toggleAccessGroup = (group: string) => {
    if (formData.access_groups.includes(group)) {
      setFormData({
        ...formData,
        access_groups: formData.access_groups.filter((g) => g !== group),
      });
    } else {
      setFormData({
        ...formData,
        access_groups: [...formData.access_groups, group],
      });
    }
  };

  const resetForm = () => {
    setFormData({
      model_alias: '',
      display_name: '',
      provider: 'openai',
      actual_model: '',
      description: '',
      pricing_input: '',
      pricing_output: '',
      credential_name: '',
      access_groups: [],
      organization_id: organizations.length > 0 ? organizations[0].organization_id : '',
    });
  };

  const getProviderBadgeColor = (provider: string) => {
    const colors: Record<string, string> = {
      openai: 'bg-green-500',
      anthropic: 'bg-orange-500',
      google: 'bg-blue-500',
      azure: 'bg-cyan-500',
      aws: 'bg-yellow-500',
    };
    return colors[provider.toLowerCase()] || 'bg-gray-500';
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Model Aliases</h1>
                <p className="text-muted-foreground">
                  Create and manage model aliases that map to actual LLM models
                </p>
              </div>
              <Button onClick={() => {
                resetForm();
                setEditingModel(null);
                setShowCreateForm(!showCreateForm);
              }}>
                <Plus className="mr-2 h-4 w-4" />
                New Model Alias
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>{editingModel ? 'Edit Model Alias' : 'Create Model Alias'}</CardTitle>
                  <CardDescription>
                    {editingModel
                      ? 'Update the model alias configuration'
                      : 'Create a user-facing alias that maps to an actual LLM model. Select a provider, choose from available models, and pricing will be auto-populated.'
                    }
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="model_alias">Model Alias *</Label>
                        <Input
                          id="model_alias"
                          placeholder="e.g., chat-fast"
                          value={formData.model_alias}
                          onChange={(e) =>
                            setFormData({ ...formData, model_alias: e.target.value })
                          }
                          required
                          disabled={!!editingModel}
                        />
                        <p className="text-xs text-muted-foreground">
                          User-facing name (cannot be changed after creation)
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="display_name">Display Name *</Label>
                        <Input
                          id="display_name"
                          placeholder="e.g., Fast Chat Model"
                          value={formData.display_name}
                          onChange={(e) =>
                            setFormData({ ...formData, display_name: e.target.value })
                          }
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="organization_id">Organization *</Label>
                        <select
                          id="organization_id"
                          value={formData.organization_id}
                          onChange={(e) => handleOrganizationChange(e.target.value)}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          required
                        >
                          <option value="">Select organization...</option>
                          {organizations.map((org) => (
                            <option key={org.organization_id} value={org.organization_id}>
                              {org.organization_id} ({org.name})
                            </option>
                          ))}
                        </select>
                        <p className="text-xs text-muted-foreground">
                          Select organization to see available credentials
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="provider">Provider *</Label>
                        <select
                          id="provider"
                          value={formData.provider}
                          onChange={(e) => handleProviderChange(e.target.value)}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          required
                        >
                          {PROVIDERS.map((provider) => (
                            <option key={provider.value} value={provider.value}>
                              {provider.label} - {provider.description}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="actual_model">Select Model *</Label>
                        <select
                          id="actual_model"
                          value={formData.actual_model}
                          onChange={(e) => handleModelChange(e.target.value)}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          required
                        >
                          <option value="">Choose a model...</option>
                          {getModelsForProvider(formData.provider).map((model) => (
                            <option key={model.value} value={model.value}>
                              {model.label} - {model.description}
                            </option>
                          ))}
                        </select>
                        <p className="text-xs text-muted-foreground">
                          Pricing will be auto-populated based on provider defaults
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="credential_name">Provider Credential</Label>
                        <select
                          id="credential_name"
                          value={formData.credential_name}
                          onChange={(e) =>
                            setFormData({ ...formData, credential_name: e.target.value })
                          }
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                          <option value="">Use environment variables</option>
                          {credentials
                            .filter(c => c.provider === formData.provider && c.is_active)
                            .map((cred) => (
                              <option key={cred.credential_id} value={cred.credential_name}>
                                {cred.credential_name} (Active)
                              </option>
                            ))}
                        </select>
                        <p className="text-xs text-muted-foreground">
                          {credentials.filter(c => c.provider === formData.provider && c.is_active).length === 0
                            ? `No active ${formData.provider} credentials found. Add credentials in Provider Credentials page.`
                            : 'Select a credential or leave empty to use environment variables'
                          }
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="pricing_input">Input Pricing (per 1M tokens)</Label>
                        <Input
                          id="pricing_input"
                          type="number"
                          step="0.01"
                          placeholder="e.g., 2.50"
                          value={formData.pricing_input}
                          onChange={(e) =>
                            setFormData({ ...formData, pricing_input: e.target.value })
                          }
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="pricing_output">Output Pricing (per 1M tokens)</Label>
                        <Input
                          id="pricing_output"
                          type="number"
                          step="0.01"
                          placeholder="e.g., 10.00"
                          value={formData.pricing_output}
                          onChange={(e) =>
                            setFormData({ ...formData, pricing_output: e.target.value })
                          }
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
                      <Label>Model Access Groups</Label>
                      {accessGroups.length > 0 ? (
                        <div className="border rounded-md p-4 space-y-2 max-h-48 overflow-y-auto">
                          {accessGroups.map((group) => (
                            <div
                              key={group.group_name}
                              className="flex items-center space-x-2 p-2 hover:bg-accent rounded cursor-pointer"
                              onClick={() => toggleAccessGroup(group.group_name)}
                            >
                              <input
                                type="checkbox"
                                checked={formData.access_groups.includes(group.group_name)}
                                onChange={() => toggleAccessGroup(group.group_name)}
                                className="h-4 w-4 rounded border-primary text-primary"
                              />
                              <div className="flex-1">
                                <div className="font-medium">{group.display_name}</div>
                                <div className="text-xs text-muted-foreground">
                                  {group.group_name} • {group.model_aliases.length} models
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No access groups available. Create access groups first to assign models.
                        </p>
                      )}
                      {formData.access_groups.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {formData.access_groups.map((group) => (
                            <Badge key={group} variant="secondary" className="cursor-pointer"
                              onClick={() => toggleAccessGroup(group)}>
                              {group} <X className="h-3 w-3 ml-1" />
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">
                        {editingModel ? 'Update Model Alias' : 'Create Model Alias'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setShowCreateForm(false);
                          setEditingModel(null);
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
                <CardTitle>Model Aliases</CardTitle>
                <CardDescription>
                  All model aliases registered in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : models.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    No model aliases yet. Create one to get started.
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Alias</TableHead>
                        <TableHead>Display Name</TableHead>
                        <TableHead>Provider</TableHead>
                        <TableHead>Actual Model</TableHead>
                        <TableHead>Access Groups</TableHead>
                        <TableHead>Pricing</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {models.map((model) => (
                        <TableRow key={model.model_alias}>
                          <TableCell className="font-mono font-semibold">
                            {model.model_alias}
                          </TableCell>
                          <TableCell>{model.display_name}</TableCell>
                          <TableCell>
                            <Badge
                              className={`${getProviderBadgeColor(model.provider)} text-white`}
                            >
                              {model.provider}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {model.actual_model}
                          </TableCell>
                          <TableCell>
                            {model.access_groups.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {model.access_groups.map((group) => (
                                  <Badge key={group} variant="outline" className="text-xs">
                                    {group}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">None</span>
                            )}
                          </TableCell>
                          <TableCell className="text-sm">
                            {model.pricing_input && model.pricing_output ? (
                              <div className="space-y-0.5">
                                <div>In: ${model.pricing_input}/1M</div>
                                <div>Out: ${model.pricing_output}/1M</div>
                              </div>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={model.status === 'active' ? 'default' : 'secondary'}
                            >
                              {model.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1 justify-end">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(model)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(model.model_alias)}
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
