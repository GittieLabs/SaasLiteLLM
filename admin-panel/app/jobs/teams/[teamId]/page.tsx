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

interface JobSummary {
  job_id: string;
  team_id: string;
  user_id: string | null;
  job_type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  retry_count: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  credit_applied: boolean;
  job_metadata: Record<string, any> | null;
}

interface JobListResponse {
  jobs: JobSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function TeamJobsPage() {
  return (
    <ProtectedRoute>
      <TeamJobsContent />
    </ProtectedRoute>
  );
}

function TeamJobsContent() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.teamId as string;

  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [jobTypeFilter, setJobTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [jobIdFilter, setJobIdFilter] = useState('');

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError('');

      const params: Record<string, string> = {
        page: page.toString(),
        page_size: pageSize.toString(),
      };

      if (statusFilter) params.status = statusFilter;
      if (jobTypeFilter) params.job_type = jobTypeFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (jobIdFilter) params.job_id_filter = jobIdFilter;

      console.log('Loading jobs for team:', teamId, 'with params:', params);
      const response: JobListResponse = await api.getTeamJobs(teamId, params);
      console.log('Jobs response:', response);

      setJobs(response.jobs);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      console.error('Failed to load jobs:', err);
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [teamId, page, statusFilter, jobTypeFilter, startDate, endDate, jobIdFilter]);

  const handleClearFilters = () => {
    setStatusFilter('');
    setJobTypeFilter('');
    setStartDate('');
    setEndDate('');
    setJobIdFilter('');
    setPage(1);
  };

  const handleJobClick = (jobId: string) => {
    router.push(`/jobs/teams/${teamId}/job/${jobId}`);
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      completed: 'default',
      in_progress: 'secondary',
      failed: 'destructive',
      pending: 'outline',
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => router.push('/teams')}
              className="mb-4"
            >
              Back to Teams
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">Team Jobs</h1>
            <p className="text-gray-600 mt-2">Team ID: {teamId}</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>Filter and search jobs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="status">Status</Label>
                  <select
                    id="status"
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setPage(1);
                    }}
                    className="w-full mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                  >
                    <option value="">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>

                <div>
                  <Label htmlFor="jobType">Job Type</Label>
                  <Input
                    id="jobType"
                    type="text"
                    value={jobTypeFilter}
                    onChange={(e) => {
                      setJobTypeFilter(e.target.value);
                      setPage(1);
                    }}
                    placeholder="e.g., chat, completion"
                  />
                </div>

                <div>
                  <Label htmlFor="jobId">Job ID</Label>
                  <Input
                    id="jobId"
                    type="text"
                    value={jobIdFilter}
                    onChange={(e) => {
                      setJobIdFilter(e.target.value);
                      setPage(1);
                    }}
                    placeholder="Search by job ID"
                  />
                </div>

                <div>
                  <Label htmlFor="startDate">Start Date</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={startDate}
                    onChange={(e) => {
                      setStartDate(e.target.value);
                      setPage(1);
                    }}
                  />
                </div>

                <div>
                  <Label htmlFor="endDate">End Date</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={endDate}
                    onChange={(e) => {
                      setEndDate(e.target.value);
                      setPage(1);
                    }}
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

          <Card>
            <CardHeader>
              <CardTitle>Jobs</CardTitle>
              <CardDescription>
                {loading ? 'Loading...' : `${total} total jobs`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">Loading jobs...</div>
              ) : jobs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No jobs found for this team.
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Job ID</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Created</TableHead>
                          <TableHead className="text-right">Calls</TableHead>
                          <TableHead className="text-right">Success</TableHead>
                          <TableHead className="text-right">Failed</TableHead>
                          <TableHead className="text-right">Retries</TableHead>
                          <TableHead className="text-right">Tokens</TableHead>
                          <TableHead className="text-right">Cost</TableHead>
                          <TableHead className="text-right">Latency</TableHead>
                          <TableHead>Credits</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {jobs.map((job) => (
                          <TableRow key={job.job_id} className="hover:bg-gray-50">
                            <TableCell className="font-mono text-xs">
                              {job.job_id.substring(0, 8)}...
                            </TableCell>
                            <TableCell>{job.job_type}</TableCell>
                            <TableCell>{getStatusBadge(job.status)}</TableCell>
                            <TableCell>
                              {new Date(job.created_at).toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">{job.total_calls}</TableCell>
                            <TableCell className="text-right text-green-600">
                              {job.successful_calls}
                            </TableCell>
                            <TableCell className="text-right text-red-600">
                              {job.failed_calls}
                            </TableCell>
                            <TableCell className="text-right">{job.retry_count}</TableCell>
                            <TableCell className="text-right">
                              {job.total_tokens.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                              ${job.total_cost_usd.toFixed(6)}
                            </TableCell>
                            <TableCell className="text-right">
                              {job.avg_latency_ms}ms
                            </TableCell>
                            <TableCell>
                              {job.credit_applied ? (
                                <Badge variant="secondary">Applied</Badge>
                              ) : (
                                <Badge variant="outline">None</Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleJobClick(job.job_id)}
                              >
                                View Details
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Pagination */}
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-gray-600">
                      Page {page} of {totalPages} ({total} total jobs)
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
