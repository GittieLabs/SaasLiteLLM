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
import { Plus, Trash2, Edit, Eye, EyeOff, Power, PowerOff } from 'lucide-react';
import { Organization } from '@/types';
import { api } from '@/lib/api-client';

interface ProviderCredential {
  credential_id: string;
  organization_id: string;
  provider: string;
  credential_name: string;
  api_key: string;
  api_base?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', description: 'GPT-4, GPT-3.5' },
  { value: 'anthropic', label: 'Anthropic', description: 'Claude 3.5, Claude 3' },
  { value: 'gemini', label: 'Google Gemini', description: 'Gemini Pro, Gemini Flash' },
  { value: 'fireworks', label: 'Fireworks AI', description: 'Llama, Mixtral' },
];

export default function ProviderCredentialsPage() {
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingCredential, setEditingCredential] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
  const [selectedOrganization, setSelectedOrganization] = useState<string>('');
  const [formData, setFormData] = useState({
    organization_id: '',
    provider: '',
    credential_name: '',
    api_key: '',
    api_base: '',
  });

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrganization) {
      loadCredentials(selectedOrganization);
    }
  }, [selectedOrganization]);

  const loadOrganizations = async () => {
    try {
      const orgsData = await api.getOrganizations();
      setOrganizations(orgsData);
      if (orgsData.length > 0 && !selectedOrganization) {
        setSelectedOrganization(orgsData[0].organization_id);
      }
    } catch (error) {
      console.error('Failed to load organizations:', error);
      setOrganizations([]);
    }
  };

  const loadCredentials = async (organizationId: string) => {
    try {
      setLoading(true);
      const data = await api.getProviderCredentials(organizationId);
      setCredentials(data);
    } catch (error) {
      console.error('Failed to load credentials:', error);
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCredential) {
        // Update existing credential
        await api.updateProviderCredential(editingCredential, {
          credential_name: formData.credential_name,
          api_key: formData.api_key,
          api_base: formData.api_base || undefined,
        });
      } else {
        // Create new credential
        await api.createProviderCredential({
          organization_id: formData.organization_id,
          provider: formData.provider,
          credential_name: formData.credential_name,
          api_key: formData.api_key,
          api_base: formData.api_base || undefined,
        });
      }

      setShowCreateForm(false);
      setEditingCredential(null);
      resetForm();
      if (selectedOrganization) {
        loadCredentials(selectedOrganization);
      }
    } catch (error: any) {
      console.error('Failed to save credential:', error);
      alert(`Failed to save credential: ${error.message}`);
    }
  };

  const handleEdit = (credential: ProviderCredential) => {
    setFormData({
      organization_id: credential.organization_id,
      provider: credential.provider,
      credential_name: credential.credential_name,
      api_key: credential.api_key,
      api_base: credential.api_base || '',
    });
    setEditingCredential(credential.credential_id);
    setShowCreateForm(true);
  };

  const handleDelete = async (credentialId: string) => {
    if (!confirm('Are you sure you want to delete this credential? This action cannot be undone.')) {
      return;
    }

    try {
      await api.deleteProviderCredential(credentialId);
      if (selectedOrganization) {
        loadCredentials(selectedOrganization);
      }
    } catch (error: any) {
      console.error('Failed to delete credential:', error);
      alert(`Failed to delete credential: ${error.message}`);
    }
  };

  const handleToggleActive = async (credential: ProviderCredential) => {
    try {
      if (credential.is_active) {
        await api.deactivateProviderCredential(credential.credential_id);
      } else {
        await api.activateProviderCredential(credential.credential_id);
      }
      if (selectedOrganization) {
        loadCredentials(selectedOrganization);
      }
    } catch (error: any) {
      console.error('Failed to toggle credential status:', error);
      alert(`Failed to toggle credential status: ${error.message}`);
    }
  };

  const resetForm = () => {
    setFormData({
      organization_id: selectedOrganization || '',
      provider: '',
      credential_name: '',
      api_key: '',
      api_base: '',
    });
  };

  const toggleKeyVisibility = (credentialId: string) => {
    setRevealedKeys((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(credentialId)) {
        newSet.delete(credentialId);
      } else {
        newSet.add(credentialId);
      }
      return newSet;
    });
  };

  const getProviderBadgeColor = (provider: string) => {
    switch (provider) {
      case 'openai':
        return 'bg-green-500';
      case 'anthropic':
        return 'bg-orange-500';
      case 'gemini':
        return 'bg-blue-500';
      case 'fireworks':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getProviderLabel = (provider: string) => {
    const providerObj = PROVIDERS.find(p => p.value === provider);
    return providerObj?.label || provider;
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Provider Credentials</h1>
                <p className="text-muted-foreground">Manage API credentials for LLM providers</p>
              </div>
              <Button
                onClick={() => {
                  resetForm();
                  setEditingCredential(null);
                  setShowCreateForm(!showCreateForm);
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Credential
              </Button>
            </div>

            <div className="mb-6">
              <Label htmlFor="org-filter">Filter by Organization</Label>
              <select
                id="org-filter"
                value={selectedOrganization}
                onChange={(e) => setSelectedOrganization(e.target.value)}
                className="mt-2 flex h-10 w-full max-w-md rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="">Select an organization...</option>
                {organizations.map((org) => (
                  <option key={org.organization_id} value={org.organization_id}>
                    {org.organization_id} ({org.name})
                  </option>
                ))}
              </select>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>{editingCredential ? 'Edit Credential' : 'Create Credential'}</CardTitle>
                  <CardDescription>
                    {editingCredential
                      ? 'Update provider API credential'
                      : 'Add a new provider API credential for an organization'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="organization_id">Organization *</Label>
                        <select
                          id="organization_id"
                          value={formData.organization_id}
                          onChange={(e) =>
                            setFormData({ ...formData, organization_id: e.target.value })
                          }
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          required
                          disabled={!!editingCredential}
                        >
                          <option value="">Select an organization...</option>
                          {organizations.map((org) => (
                            <option key={org.organization_id} value={org.organization_id}>
                              {org.organization_id} ({org.name})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="provider">Provider *</Label>
                        <select
                          id="provider"
                          value={formData.provider}
                          onChange={(e) =>
                            setFormData({ ...formData, provider: e.target.value })
                          }
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          required
                          disabled={!!editingCredential}
                        >
                          <option value="">Select a provider...</option>
                          {PROVIDERS.map((provider) => (
                            <option key={provider.value} value={provider.value}>
                              {provider.label} - {provider.description}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="credential_name">Credential Name *</Label>
                      <Input
                        id="credential_name"
                        placeholder="e.g., Production API Key, Development Key"
                        value={formData.credential_name}
                        onChange={(e) =>
                          setFormData({ ...formData, credential_name: e.target.value })
                        }
                        required
                      />
                      <p className="text-xs text-muted-foreground">
                        A friendly name to identify this credential
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="api_key">API Key *</Label>
                      <Input
                        id="api_key"
                        type="password"
                        placeholder="sk-..."
                        value={formData.api_key}
                        onChange={(e) =>
                          setFormData({ ...formData, api_key: e.target.value })
                        }
                        required
                      />
                      <p className="text-xs text-muted-foreground">
                        The API key will be encrypted before storage
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="api_base">API Base URL (Optional)</Label>
                      <Input
                        id="api_base"
                        placeholder="https://api.openai.com/v1"
                        value={formData.api_base}
                        onChange={(e) =>
                          setFormData({ ...formData, api_base: e.target.value })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Custom API endpoint (leave empty to use provider default)
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">
                        {editingCredential ? 'Update Credential' : 'Create Credential'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setShowCreateForm(false);
                          setEditingCredential(null);
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
                <CardTitle>Provider Credentials</CardTitle>
                <CardDescription>
                  {selectedOrganization
                    ? `Credentials for ${selectedOrganization}`
                    : 'Select an organization to view credentials'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!selectedOrganization ? (
                  <div className="text-center text-muted-foreground py-8">
                    Select an organization to view credentials
                  </div>
                ) : loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : credentials.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    No credentials yet. Create one to get started.
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Provider</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>API Key</TableHead>
                        <TableHead>API Base</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {credentials.map((credential) => {
                        const isKeyRevealed = revealedKeys.has(credential.credential_id);

                        return (
                          <TableRow key={credential.credential_id}>
                            <TableCell>
                              <Badge
                                className={`${getProviderBadgeColor(credential.provider)} text-white`}
                              >
                                {getProviderLabel(credential.provider)}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium">
                              {credential.credential_name}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm">
                                  {isKeyRevealed
                                    ? credential.api_key
                                    : credential.api_key.substring(0, 10) + '...'}
                                </span>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleKeyVisibility(credential.credential_id)}
                                >
                                  {isKeyRevealed ? (
                                    <EyeOff className="h-4 w-4" />
                                  ) : (
                                    <Eye className="h-4 w-4" />
                                  )}
                                </Button>
                              </div>
                            </TableCell>
                            <TableCell className="font-mono text-xs">
                              {credential.api_base || 'Default'}
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={`${
                                  credential.is_active ? 'bg-green-500' : 'bg-gray-500'
                                } text-white`}
                              >
                                {credential.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {new Date(credential.created_at).toLocaleDateString()}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex gap-1 justify-end">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleToggleActive(credential)}
                                  title={
                                    credential.is_active
                                      ? 'Deactivate credential'
                                      : 'Activate credential'
                                  }
                                >
                                  {credential.is_active ? (
                                    <PowerOff className="h-4 w-4 text-yellow-500" />
                                  ) : (
                                    <Power className="h-4 w-4 text-green-500" />
                                  )}
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEdit(credential)}
                                  title="Edit credential"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(credential.credential_id)}
                                  title="Delete credential"
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
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
