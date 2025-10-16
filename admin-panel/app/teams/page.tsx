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
import { Team } from '@/types';
import { api } from '@/lib/api-client';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    team_alias: '',
    organization_id: '',
    credits_allocated: 1000,
  });

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const teams = await api.getTeams();
      setTeams(teams);
    } catch (error) {
      console.error('Failed to load teams:', error);
      setTeams([]); // Show empty list on error
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createTeam(formData);
      setShowCreateForm(false);
      setFormData({ team_alias: '', organization_id: '', credits_allocated: 1000 });
      loadTeams();
    } catch (error) {
      console.error('Failed to create team:', error);
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
                <p className="text-muted-foreground">Manage teams and their credits</p>
              </div>
              <Button onClick={() => setShowCreateForm(!showCreateForm)}>
                <Plus className="mr-2 h-4 w-4" />
                New Team
              </Button>
            </div>

            {showCreateForm && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Create Team</CardTitle>
                  <CardDescription>Add a new team to an organization</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="team_alias">Team Name</Label>
                      <Input
                        id="team_alias"
                        value={formData.team_alias}
                        onChange={(e) => setFormData({ ...formData, team_alias: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="organization_id">Organization ID</Label>
                      <Input
                        id="organization_id"
                        value={formData.organization_id}
                        onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="credits">Initial Credits</Label>
                      <Input
                        id="credits"
                        type="number"
                        value={formData.credits_allocated}
                        onChange={(e) => setFormData({ ...formData, credits_allocated: Number(e.target.value) })}
                        required
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
                <CardTitle>Teams List</CardTitle>
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
                        <TableHead>Organization</TableHead>
                        <TableHead>Virtual Key</TableHead>
                        <TableHead>Credits Used</TableHead>
                        <TableHead>Credits Remaining</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {teams.map((team) => (
                        <TableRow key={team.team_id}>
                          <TableCell className="font-mono text-sm">{team.team_id}</TableCell>
                          <TableCell className="font-medium">{team.team_alias}</TableCell>
                          <TableCell>{team.organization_id}</TableCell>
                          <TableCell className="font-mono text-sm">{team.virtual_key || 'N/A'}</TableCell>
                          <TableCell>
                            {team.credits?.credits_used?.toLocaleString() ?? 'N/A'}
                          </TableCell>
                          <TableCell>
                            {team.credits?.credits_remaining !== undefined ? (
                              <span className="font-semibold text-green-600">
                                {team.credits.credits_remaining.toLocaleString()}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">N/A</span>
                            )}
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
