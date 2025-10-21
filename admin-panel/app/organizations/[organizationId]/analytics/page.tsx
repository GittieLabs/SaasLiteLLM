'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface OrganizationAnalytics {
  organization_id: string;
  organization_name: string | null;
  total_spend: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  daily_spend: Array<{
    date: string;
    spend: number;
  }>;
  spend_per_team: Array<{
    team_id: string;
    spend: number;
    successful: number;
    failed: number;
    tokens: number;
  }>;
  top_models: Array<{
    model: string;
    spend: number;
    count: number;
  }>;
  provider_usage: Array<{
    provider: string;
    spend: number;
    successful: number;
    failed: number;
    tokens: number;
  }>;
}

interface OrganizationJobStats {
  organization_id: string;
  organization_name: string | null;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  in_progress_jobs: number;
  total_teams: number;
  total_llm_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  total_credits_used: number;
  top_teams: Array<{
    team_id: string;
    job_count: number;
    credits_used: number;
  }>;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: '#10A37F',
  anthropic: '#D97706',
  google: '#4285F4',
  meta: '#0668E1',
  other: '#6B7280'
};

export default function OrganizationAnalyticsPage() {
  return (
    <ProtectedRoute>
      <OrganizationAnalyticsContent />
    </ProtectedRoute>
  );
}

function OrganizationAnalyticsContent() {
  const params = useParams();
  const router = useRouter();
  const organizationId = params.organizationId as string;

  const [analytics, setAnalytics] = useState<OrganizationAnalytics | null>(null);
  const [jobStats, setJobStats] = useState<OrganizationJobStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Date filters
  const [startDate, setStartDate] = useState('');
  const [endDate] = useState('');

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError('');

      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [analyticsResponse, jobStatsResponse] = await Promise.all([
        api.getOrganizationAnalytics(organizationId, params),
        api.getOrganizationJobStats(organizationId, params)
      ]);

      setAnalytics(analyticsResponse);
      setJobStats(jobStatsResponse);
    } catch (err: any) {
      console.error('Failed to load organization analytics:', err);
      setError(err.message || 'Failed to load organization analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [organizationId, startDate, endDate]);

  const handleClearFilters = () => {
    setStartDate('');
    setEndDate('');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="text-center py-8">Loading organization analytics...</div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="bg-destructive/15 border border-destructive text-destructive px-4 py-3 rounded">
            {error}
          </div>
        </main>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="text-center py-8 text-muted-foreground">
            Organization not found.
          </div>
        </main>
      </div>
    );
  }

  const successRate = analytics.total_requests > 0
    ? ((analytics.successful_requests / analytics.total_requests) * 100).toFixed(1)
    : '0';

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => router.push('/organizations')}
              className="mb-4"
            >
              Back to Organizations
            </Button>
            <h1 className="text-3xl font-bold">Organization Analytics</h1>
            {analytics.organization_name && (
              <p className="text-muted-foreground mt-2">{analytics.organization_name}</p>
            )}
          </div>

          {/* Date Filters */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>Filter analytics by date range</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="startDate">Start Date</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="endDate">End Date</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>

                <div className="flex items-end">
                  <Button
                    variant="outline"
                    onClick={handleClearFilters}
                    className="w-full"
                  >
                    Clear Filters
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Spend</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">${analytics.total_spend.toFixed(2)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Requests</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{analytics.total_requests}</div>
                <div className="text-sm text-muted-foreground mt-1">
                  {successRate}% success rate
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Successful Requests</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">{analytics.successful_requests}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Failed Requests</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-red-600">{analytics.failed_requests}</div>
              </CardContent>
            </Card>
          </div>

          {/* Daily Spend Chart */}
          {analytics.daily_spend.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Daily Spend</CardTitle>
                <CardDescription>Spend over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics.daily_spend}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                      formatter={(value: number) => `$${value.toFixed(6)}`}
                    />
                    <Bar dataKey="spend" fill="#0ea5e9" name="Spend (USD)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Spend Per Team */}
          {analytics.spend_per_team.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Spend Per Team</CardTitle>
                <CardDescription>Top 5 teams by spend</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analytics.spend_per_team.slice(0, 5)} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis type="number" className="text-xs" />
                      <YAxis type="category" dataKey="team_id" className="text-xs" width={150} />
                      <Tooltip
                        contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                        formatter={(value: number) => `$${value.toFixed(6)}`}
                      />
                      <Bar dataKey="spend" fill="#0ea5e9" name="Spend (USD)" />
                    </BarChart>
                  </ResponsiveContainer>

                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Team</TableHead>
                          <TableHead className="text-right">Spend</TableHead>
                          <TableHead className="text-right">Successful</TableHead>
                          <TableHead className="text-right">Failed</TableHead>
                          <TableHead className="text-right">Tokens</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {analytics.spend_per_team.slice(0, 5).map((team) => (
                          <TableRow key={team.team_id}>
                            <TableCell className="font-mono text-sm">{team.team_id}</TableCell>
                            <TableCell className="text-right">${team.spend.toFixed(4)}</TableCell>
                            <TableCell className="text-right text-green-600">{team.successful}</TableCell>
                            <TableCell className="text-right text-red-600">{team.failed}</TableCell>
                            <TableCell className="text-right">{team.tokens.toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Top Models */}
          {analytics.top_models.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Top Models</CardTitle>
                <CardDescription>Top models by spend</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics.top_models.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="model" className="text-xs" angle={-45} textAnchor="end" height={100} />
                    <YAxis className="text-xs" />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                      formatter={(value: number) => `$${value.toFixed(6)}`}
                    />
                    <Bar dataKey="spend" fill="#0ea5e9" name="Spend (USD)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Provider Usage */}
          {analytics.provider_usage.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Provider Usage</CardTitle>
                <CardDescription>Breakdown by provider</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={analytics.provider_usage}
                        dataKey="spend"
                        nameKey="provider"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label={(entry: any) => `${entry.provider}: $${entry.spend.toFixed(3)}`}
                      >
                        {analytics.provider_usage.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PROVIDER_COLORS[entry.provider] || PROVIDER_COLORS.other} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                        formatter={(value: number) => `$${value.toFixed(6)}`}
                      />
                    </PieChart>
                  </ResponsiveContainer>

                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Provider</TableHead>
                          <TableHead className="text-right">Spend</TableHead>
                          <TableHead className="text-right">Successful</TableHead>
                          <TableHead className="text-right">Failed</TableHead>
                          <TableHead className="text-right">Tokens</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {analytics.provider_usage.map((provider) => (
                          <TableRow key={provider.provider}>
                            <TableCell className="font-medium capitalize">{provider.provider}</TableCell>
                            <TableCell className="text-right">${provider.spend.toFixed(4)}</TableCell>
                            <TableCell className="text-right text-green-600">{provider.successful}</TableCell>
                            <TableCell className="text-right text-red-600">{provider.failed}</TableCell>
                            <TableCell className="text-right">{provider.tokens.toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
