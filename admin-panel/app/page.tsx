'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Users, Layers, DollarSign } from 'lucide-react';
import { api } from '@/lib/api-client';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    organizations: 0,
    teams: 0,
    modelGroups: 0,
    totalCredits: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);

        // Fetch real data from API
        const [orgs, teams, modelGroups] = await Promise.all([
          api.getOrganizations().catch(() => []),
          api.getTeams().catch(() => []),
          api.getModelGroups().catch(() => []),
        ]);

        // Calculate total credits from all teams
        const totalCredits = teams.reduce((sum: number, team: any) => {
          return sum + (team.credits_allocated || 0);
        }, 0);

        setStats({
          organizations: orgs.length,
          teams: teams.length,
          modelGroups: modelGroups.length,
          totalCredits,
        });
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8">
              <h1 className="text-3xl font-bold">Dashboard</h1>
              <p className="text-muted-foreground">Overview of your LiteLLM infrastructure</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Organizations</CardTitle>
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? '...' : stats.organizations}
                  </div>
                  <p className="text-xs text-muted-foreground">Active organizations</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Teams</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? '...' : stats.teams}
                  </div>
                  <p className="text-xs text-muted-foreground">Total teams</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Model Groups</CardTitle>
                  <Layers className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? '...' : stats.modelGroups}
                  </div>
                  <p className="text-xs text-muted-foreground">Configured groups</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? '...' : stats.totalCredits.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">Allocated credits</p>
                </CardContent>
              </Card>
            </div>

            {loading && (
              <div className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle>Loading...</CardTitle>
                    <CardDescription>Fetching dashboard data</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">Please wait...</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
