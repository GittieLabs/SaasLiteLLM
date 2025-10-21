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

export default function OrganizationJobsPage() {
  return (
    <ProtectedRoute>
      <OrganizationJobsContent />
    </ProtectedRoute>
  );
}

function OrganizationJobsContent() {
  const params = useParams();
  const router = useRouter();
  const organizationId = params.organizationId as string;

  const [stats, setStats] = useState<OrganizationJobStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Date filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const loadStats = async () => {
    try {
      setLoading(true);
      setError('');

      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: OrganizationJobStats = await api.getOrganizationJobStats(organizationId, params);
      setStats(response);
    } catch (err: any) {
      console.error('Failed to load organization stats:', err);
      setError(err.message || 'Failed to load organization stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [organizationId, startDate, endDate]);

  const handleClearFilters = () => {
    setStartDate('');
    setEndDate('');
  };

  const handleViewTeamJobs = (teamId: string) => {
    router.push(`/jobs/teams/${teamId}`);
  };

  const calculateSuccessRate = () => {
    if (!stats || stats.total_llm_calls === 0) return 0;
    return ((stats.successful_calls / stats.total_llm_calls) * 100).toFixed(1);
  };

  const calculateJobCompletionRate = () => {
    if (!stats || stats.total_jobs === 0) return 0;
    return ((stats.completed_jobs / stats.total_jobs) * 100).toFixed(1);
  };

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
            <h1 className="text-3xl font-bold">Organization Job Analytics</h1>
            {stats && stats.organization_name && (
              <p className="text-muted-foreground mt-2">{stats.organization_name}</p>
            )}
            <p className="text-muted-foreground text-sm mt-1">Organization ID: {organizationId}</p>
          </div>

          {error && (
            <div className="bg-destructive/15 border border-destructive text-destructive px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* Date Filters */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>Filter statistics by date range</CardDescription>
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

          {loading ? (
            <div className="text-center py-8">Loading organization statistics...</div>
          ) : stats ? (
            <>
              {/* Overview Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total Jobs</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{stats.total_jobs}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      {calculateJobCompletionRate()}% completion rate
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total Teams</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{stats.total_teams}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      Active teams in organization
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total LLM Calls</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {stats.total_llm_calls.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {calculateSuccessRate()}% success rate
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total Cost</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      ${stats.total_cost_usd.toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {stats.total_credits_used} credits used
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Job Status Breakdown */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Job Status Breakdown</CardTitle>
                  <CardDescription>Distribution of jobs by status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="flex items-center justify-between p-4">
                        <div>
                          <div className="text-sm text-muted-foreground">Completed</div>
                          <div className="text-2xl font-bold">
                            {stats.completed_jobs}
                          </div>
                        </div>
                        <Badge variant="default">
                          {stats.total_jobs > 0
                            ? ((stats.completed_jobs / stats.total_jobs) * 100).toFixed(0)
                            : 0}%
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="flex items-center justify-between p-4">
                        <div>
                          <div className="text-sm text-muted-foreground">In Progress</div>
                          <div className="text-2xl font-bold">
                            {stats.in_progress_jobs}
                          </div>
                        </div>
                        <Badge variant="secondary">
                          {stats.total_jobs > 0
                            ? ((stats.in_progress_jobs / stats.total_jobs) * 100).toFixed(0)
                            : 0}%
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="flex items-center justify-between p-4">
                        <div>
                          <div className="text-sm text-muted-foreground">Failed</div>
                          <div className="text-2xl font-bold">
                            {stats.failed_jobs}
                          </div>
                        </div>
                        <Badge variant="destructive">
                          {stats.total_jobs > 0
                            ? ((stats.failed_jobs / stats.total_jobs) * 100).toFixed(0)
                            : 0}%
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="flex items-center justify-between p-4">
                        <div>
                          <div className="text-sm text-muted-foreground">Pending</div>
                          <div className="text-2xl font-bold">
                            {stats.total_jobs - stats.completed_jobs - stats.in_progress_jobs - stats.failed_jobs}
                          </div>
                        </div>
                        <Badge variant="outline">
                          {stats.total_jobs > 0
                            ? (((stats.total_jobs - stats.completed_jobs - stats.in_progress_jobs - stats.failed_jobs) / stats.total_jobs) * 100).toFixed(0)
                            : 0}%
                        </Badge>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>

              {/* LLM Call Metrics */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>LLM Call Metrics</CardTitle>
                  <CardDescription>Aggregated metrics across all jobs</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg">
                      <div className="text-sm text-gray-600">Total Calls</div>
                      <div className="text-2xl font-bold">
                        {stats.total_llm_calls.toLocaleString()}
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="text-sm text-gray-600">Successful Calls</div>
                      <div className="text-2xl font-bold text-green-600">
                        {stats.successful_calls.toLocaleString()}
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="text-sm text-gray-600">Failed Calls</div>
                      <div className="text-2xl font-bold text-red-600">
                        {stats.failed_calls.toLocaleString()}
                      </div>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <div className="text-sm text-gray-600">Total Tokens</div>
                      <div className="text-2xl font-bold">
                        {stats.total_tokens.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Top Teams */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Teams by Job Count</CardTitle>
                  <CardDescription>
                    Teams with the most job activity
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {stats.top_teams.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      No team data available.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>Team ID</TableHead>
                            <TableHead className="text-right">Job Count</TableHead>
                            <TableHead className="text-right">Credits Used</TableHead>
                            <TableHead className="text-right">% of Total Jobs</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {stats.top_teams.map((team, index) => (
                            <TableRow key={team.team_id}>
                              <TableCell>
                                <Badge variant={index < 3 ? 'default' : 'outline'}>
                                  #{index + 1}
                                </Badge>
                              </TableCell>
                              <TableCell className="font-mono text-sm">
                                {team.team_id}
                              </TableCell>
                              <TableCell className="text-right font-medium">
                                {team.job_count.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-right">
                                {team.credits_used.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-right">
                                {stats.total_jobs > 0
                                  ? ((team.job_count / stats.total_jobs) * 100).toFixed(1)
                                  : 0}%
                              </TableCell>
                              <TableCell>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleViewTeamJobs(team.team_id)}
                                >
                                  View Jobs
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Organization not found.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
