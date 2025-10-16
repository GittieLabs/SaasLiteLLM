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
import { Plus, Trash2, Edit, Eye, EyeOff, Copy, X, Pause, Play } from 'lucide-react';
import { Team, ModelAccessGroup } from '@/types';
import { api } from '@/lib/api-client';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [accessGroups, setAccessGroups] = useState<ModelAccessGroup[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTeam, setEditingTeam] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
  const [formData, setFormData] = useState({
    team_id: '',
    organization_id: '',
    access_groups: [] as string[],
    credits_allocated: 1000,
    credits_used: 0,
    budget_mode: 'job_based' as 'job_based' | 'consumption_usd' | 'consumption_tokens',
    credits_per_dollar: 10.0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [teamsData, groupsData] = await Promise.all([
        api.getTeams(),
        api.getModelAccessGroups(),
      ]);
      setTeams(teamsData);
      setAccessGroups(groupsData);
    } catch (error) {
      console.error('Failed to load data:', error);
      setTeams([]);
      setAccessGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTeam) {
        // Update existing team
        await api.updateTeam(editingTeam, {
          access_groups: formData.access_groups,
          credits_allocated: formData.credits_allocated,
          credits_used: formData.credits_used,
          budget_mode: formData.budget_mode,
          credits_per_dollar: formData.credits_per_dollar,
        });
      } else {
        // Create new team
        await api.createTeam({
          team_id: formData.team_id,
          organization_id: formData.organization_id,
          access_groups: formData.access_groups,
          credits_allocated: formData.credits_allocated,
        });
      }

      setShowCreateForm(false);
      setEditingTeam(null);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error('Failed to save team:', error);
      alert(`Failed to save team: ${error.message}`);
    }
  };

  const handleEdit = (team: Team) => {
    setFormData({
      team_id: team.team_id,
      organization_id: team.organization_id,
      access_groups: team.access_groups || [],
      credits_allocated: team.credits_allocated || 0,
      credits_used: team.credits_used || 0,
      budget_mode: (team.budget_mode || 'job_based') as 'job_based' | 'consumption_usd' | 'consumption_tokens',
      credits_per_dollar: team.credits_per_dollar || 10.0,
    });
    setEditingTeam(team.team_id);
    setShowCreateForm(true);
  };

  const handleDelete = async (teamId: string) => {
    if (teamId.endsWith('_default')) {
      alert('Cannot delete default teams. Default teams are protected from deletion.');
      return;
    }

    if (!confirm(`Are you sure you want to delete team "${teamId}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.deleteTeam(teamId);
      loadData();
    } catch (error: any) {
      console.error('Failed to delete team:', error);
      alert(`Failed to delete team: ${error.message}`);
    }
  };

  const handleSuspend = async (teamId: string) => {
    if (!confirm(`Suspend team "${teamId}"? They will not be able to make API calls until resumed.`)) {
      return;
    }

    try {
      await api.suspendTeam(teamId);
      loadData();
    } catch (error: any) {
      console.error('Failed to suspend team:', error);
      alert(`Failed to suspend team: ${error.message}`);
    }
  };

  const handleResume = async (teamId: string) => {
    if (!confirm(`Resume team "${teamId}"? They will be able to make API calls again.`)) {
      return;
    }

    try {
      await api.resumeTeam(teamId);
      loadData();
    } catch (error: any) {
      console.error('Failed to resume team:', error);
      alert(`Failed to resume team: ${error.message}`);
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
      team_id: '',
      organization_id: '',
      access_groups: [],
      credits_allocated: 1000,
      credits_used: 0,
      budget_mode: 'job_based',
      credits_per_dollar: 10.0,
    });
  };

  const toggleKeyVisibility = (teamId: string) => {
    setRevealedKeys((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(teamId)) {
        newSet.delete(teamId);
      } else {
        newSet.add(teamId);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
      alert('Failed to copy to clipboard');
    }
  };

  const getBudgetModeBadgeColor = (mode: string) => {
    switch (mode) {
      case 'job_based':
        return 'bg-blue-500';
      case 'consumption_usd':
        return 'bg-green-500';
      case 'consumption_tokens':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getBudgetModeLabel = (mode: string) => {
    switch (mode) {
      case 'job_based':
        return 'Job-Based';
      case 'consumption_usd':
        return 'USD-Based';
      case 'consumption_tokens':
        return 'Token-Based';
      default:
        return mode;
    }
  };

  const getCreditsPercentage = (remaining: number, total: number) => {
    if (total === 0) return 0;
    return Math.round((remaining / total) * 100);
  };

  const getCreditsColor = (percentage: number) => {
    if (percentage > 50) return 'text-green-600';
    if (percentage > 20) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'suspended':
        return 'bg-red-500';
      case 'paused':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'suspended':
        return 'Suspended';
      case 'paused':
        return 'Paused';
      default:
        return status;
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
                <h1 className="text-3xl font-bold">Teams</h1>
                <p className="text-muted-foreground">Manage teams, credits, and model access</p>
              </div>
              <Button
                onClick={() => {
                  resetForm();
                  setEditingTeam(null);
                  setShowCreateForm(!showCreateForm);
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Team
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>{editingTeam ? 'Edit Team' : 'Create Team'}</CardTitle>
                  <CardDescription>
                    {editingTeam
                      ? 'Update team configuration, credits, and budget mode'
                      : 'Create a new team with model access and credit allocation'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="team_id">Team ID *</Label>
                        <Input
                          id="team_id"
                          placeholder="e.g., team-alpha"
                          value={formData.team_id}
                          onChange={(e) =>
                            setFormData({ ...formData, team_id: e.target.value })
                          }
                          required
                          disabled={!!editingTeam}
                        />
                        <p className="text-xs text-muted-foreground">
                          Unique identifier (cannot be changed after creation)
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="organization_id">Organization ID *</Label>
                        <Input
                          id="organization_id"
                          placeholder="e.g., org-1"
                          value={formData.organization_id}
                          onChange={(e) =>
                            setFormData({ ...formData, organization_id: e.target.value })
                          }
                          required
                          disabled={!!editingTeam}
                        />
                      </div>
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
                          No access groups available. Create access groups first.
                        </p>
                      )}
                      {formData.access_groups.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {formData.access_groups.map((group) => {
                            const accessGroup = accessGroups.find(g => g.group_name === group);
                            return (
                              <Badge
                                key={group}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => toggleAccessGroup(group)}
                              >
                                {accessGroup?.display_name || group} <X className="h-3 w-3 ml-1" />
                              </Badge>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="budget_mode">Budget Mode *</Label>
                        <select
                          id="budget_mode"
                          value={formData.budget_mode}
                          onChange={(e) => setFormData({ ...formData, budget_mode: e.target.value as any })}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                          required
                        >
                          <option value="job_based">Job-Based (1 credit per job)</option>
                          <option value="consumption_usd">USD-Based (based on actual cost)</option>
                          <option value="consumption_tokens">Token-Based (based on tokens used)</option>
                        </select>
                        <p className="text-xs text-muted-foreground">
                          {formData.budget_mode === 'job_based' && 'Each completed job deducts 1 credit'}
                          {formData.budget_mode === 'consumption_usd' && 'Credits deducted based on $ cost'}
                          {formData.budget_mode === 'consumption_tokens' && '1 credit = 10,000 tokens'}
                        </p>
                      </div>

                      {formData.budget_mode === 'consumption_usd' && (
                        <div className="space-y-2">
                          <Label htmlFor="credits_per_dollar">Credits per Dollar</Label>
                          <Input
                            id="credits_per_dollar"
                            type="number"
                            step="0.1"
                            placeholder="e.g., 10"
                            value={formData.credits_per_dollar}
                            onChange={(e) =>
                              setFormData({ ...formData, credits_per_dollar: parseFloat(e.target.value) })
                            }
                          />
                          <p className="text-xs text-muted-foreground">
                            Conversion rate: 1 USD = {formData.credits_per_dollar} credits
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="credits_allocated">Credits Allocated *</Label>
                        <Input
                          id="credits_allocated"
                          type="number"
                          value={formData.credits_allocated}
                          onChange={(e) =>
                            setFormData({ ...formData, credits_allocated: Number(e.target.value) })
                          }
                          required
                        />
                        <p className="text-xs text-muted-foreground">Total credits available</p>
                      </div>

                      {editingTeam && (
                        <div className="space-y-2">
                          <Label htmlFor="credits_used">Credits Used</Label>
                          <Input
                            id="credits_used"
                            type="number"
                            value={formData.credits_used}
                            onChange={(e) =>
                              setFormData({ ...formData, credits_used: Number(e.target.value) })
                            }
                          />
                          <p className="text-xs text-muted-foreground">
                            Remaining: {formData.credits_allocated - formData.credits_used}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit">
                        {editingTeam ? 'Update Team' : 'Create Team'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setShowCreateForm(false);
                          setEditingTeam(null);
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
                <CardTitle>Teams List</CardTitle>
                <CardDescription>
                  All teams in the system with their credit allocations
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : teams.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    No teams yet. Create one to get started.
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Team ID</TableHead>
                        <TableHead>Organization</TableHead>
                        <TableHead>Access Groups</TableHead>
                        <TableHead>Virtual Key</TableHead>
                        <TableHead>Budget Mode</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Credits</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {teams.map((team) => {
                        const isKeyRevealed = revealedKeys.has(team.team_id);
                        const creditsRemaining = team.credits_remaining || 0;
                        const creditsTotal = team.credits_allocated || 0;
                        const percentage = getCreditsPercentage(creditsRemaining, creditsTotal);
                        const isDefaultTeam = team.team_id.endsWith('_default');

                        return (
                          <TableRow key={team.team_id}>
                            <TableCell className="font-mono font-semibold">
                              {team.team_id}
                              {isDefaultTeam && (
                                <Badge variant="outline" className="ml-2 text-xs">
                                  Default
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>{team.organization_id}</TableCell>
                            <TableCell>
                              {team.access_groups && team.access_groups.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {team.access_groups.map((group) => (
                                    <Badge key={group} variant="outline" className="text-xs">
                                      {group}
                                    </Badge>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-muted-foreground text-sm">No groups</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm">
                                  {team.virtual_key ? (
                                    isKeyRevealed ? team.virtual_key : team.virtual_key.substring(0, 20) + '...'
                                  ) : (
                                    'N/A'
                                  )}
                                </span>
                                {team.virtual_key && (
                                  <>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => toggleKeyVisibility(team.team_id)}
                                    >
                                      {isKeyRevealed ? (
                                        <EyeOff className="h-4 w-4" />
                                      ) : (
                                        <Eye className="h-4 w-4" />
                                      )}
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => copyToClipboard(team.virtual_key)}
                                    >
                                      <Copy className="h-4 w-4" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={`${getBudgetModeBadgeColor(team.budget_mode || 'job_based')} text-white`}
                              >
                                {getBudgetModeLabel(team.budget_mode || 'job_based')}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={`${getStatusBadgeColor(team.status || 'active')} text-white`}
                              >
                                {getStatusLabel(team.status || 'active')}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div className={`font-semibold ${getCreditsColor(percentage)}`}>
                                  {creditsRemaining.toLocaleString()} / {creditsTotal.toLocaleString()}
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className={`h-2 rounded-full ${
                                      percentage > 50 ? 'bg-green-500' :
                                      percentage > 20 ? 'bg-yellow-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${percentage}%` }}
                                  />
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  {percentage}% remaining
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex gap-1 justify-end">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEdit(team)}
                                  title="Edit team"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                {team.status === 'active' ? (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleSuspend(team.team_id)}
                                    title="Suspend team"
                                  >
                                    <Pause className="h-4 w-4 text-yellow-500" />
                                  </Button>
                                ) : (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleResume(team.team_id)}
                                    title="Resume team"
                                  >
                                    <Play className="h-4 w-4 text-green-500" />
                                  </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(team.team_id)}
                                  disabled={isDefaultTeam}
                                  title={isDefaultTeam ? 'Cannot delete default team' : 'Delete team'}
                                >
                                  <Trash2 className={`h-4 w-4 ${isDefaultTeam ? 'text-gray-400' : 'text-red-500'}`} />
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
