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
    // Fetch real stats from API
    const loadStats = async () => {
      try {
        setLoading(true);
        const data = await api.getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        // Keep stats at 0 on error
      } finally {
        setLoading(false);
      }
    };

    loadStats();
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
                  <div className="text-2xl font-bold">{stats.organizations}</div>
                  <p className="text-xs text-muted-foreground">Active organizations</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Teams</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.teams}</div>
                  <p className="text-xs text-muted-foreground">Total teams</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Model Groups</CardTitle>
                  <Layers className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.modelGroups}</div>
                  <p className="text-xs text-muted-foreground">Configured groups</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalCredits.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground">Allocated credits</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
