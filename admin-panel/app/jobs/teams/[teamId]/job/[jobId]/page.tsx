'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';

interface LLMCallDetail {
  call_id: string;
  model_used: string | null;
  model_group_used: string | null;
  resolved_model: string | null;
  purpose: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  input_cost_usd: number;
  output_cost_usd: number;
  provider_cost_usd: number;
  client_cost_usd: number;
  model_pricing_input: number | null;
  model_pricing_output: number | null;
  latency_ms: number | null;
  created_at: string;
  error: string | null;
  request_data: Record<string, any> | null;
  response_data: Record<string, any> | null;
}

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

interface JobDetail {
  job: JobSummary;
  calls: LLMCallDetail[];
}

export default function JobDetailPage() {
  return (
    <ProtectedRoute>
      <JobDetailContent />
    </ProtectedRoute>
  );
}

function JobDetailContent() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.teamId as string;
  const jobId = params.jobId as string;

  const [jobDetail, setJobDetail] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedCall, setExpandedCall] = useState<string | null>(null);

  useEffect(() => {
    const loadJobDetail = async () => {
      try {
        setLoading(true);
        setError('');

        const response: JobDetail = await api.getJobDetail(teamId, jobId);
        setJobDetail(response);
      } catch (err: any) {
        console.error('Failed to load job detail:', err);
        setError(err.message || 'Failed to load job detail');
      } finally {
        setLoading(false);
      }
    };

    loadJobDetail();
  }, [teamId, jobId]);

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      completed: 'default',
      in_progress: 'secondary',
      failed: 'destructive',
      pending: 'outline',
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const toggleCallExpansion = (callId: string) => {
    setExpandedCall(expandedCall === callId ? null : callId);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => router.push(`/jobs/teams/${teamId}`)}
              className="mb-4"
            >
              Back to Jobs
            </Button>
            <h1 className="text-3xl font-bold">Job Details</h1>
            <p className="text-muted-foreground mt-2 font-mono text-sm">Job ID: {jobId}</p>
          </div>

          {error && (
            <div className="bg-destructive/15 border border-destructive text-destructive px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">Loading job details...</div>
          ) : jobDetail ? (
            <>
              {/* Job Summary Card */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Job Summary</CardTitle>
                  <CardDescription>Overview of job execution</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Type</div>
                      <div className="font-medium">{jobDetail.job.job_type}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Status</div>
                      <div>{getStatusBadge(jobDetail.job.status)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Created</div>
                      <div className="font-medium">
                        {new Date(jobDetail.job.created_at).toLocaleString()}
                      </div>
                    </div>
                    {jobDetail.job.completed_at && (
                      <div>
                        <div className="text-sm text-muted-foreground">Completed</div>
                        <div className="font-medium">
                          {new Date(jobDetail.job.completed_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                    <div>
                      <div className="text-sm text-muted-foreground">Total Calls</div>
                      <div className="font-medium">{jobDetail.job.total_calls}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Successful Calls</div>
                      <div className="font-medium text-green-600">
                        {jobDetail.job.successful_calls}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Failed Calls</div>
                      <div className="font-medium text-red-600">
                        {jobDetail.job.failed_calls}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Retries</div>
                      <div className="font-medium">{jobDetail.job.retry_count}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Total Tokens</div>
                      <div className="font-medium">
                        {jobDetail.job.total_tokens.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Total Cost</div>
                      <div className="font-medium">
                        ${jobDetail.job.total_cost_usd.toFixed(6)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Avg Latency</div>
                      <div className="font-medium">{jobDetail.job.avg_latency_ms}ms</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Credits Applied</div>
                      <div>
                        {jobDetail.job.credit_applied ? (
                          <Badge variant="secondary">Yes</Badge>
                        ) : (
                          <Badge variant="outline">No</Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  {jobDetail.job.job_metadata && Object.keys(jobDetail.job.job_metadata).length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="text-sm text-muted-foreground mb-2">Job Metadata</div>
                      <pre className="bg-muted/50 p-3 rounded text-xs overflow-x-auto border">
                        {JSON.stringify(jobDetail.job.job_metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Cost Breakdown Card */}
              <Card className="mb-6 border-2 border-blue-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    Cost Breakdown
                    <Badge variant="outline" className="text-xs">Critical Business Metrics</Badge>
                  </CardTitle>
                  <CardDescription>Understanding your profit margins</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">Provider Cost (What YOU Pay)</div>
                      <div className="text-2xl font-bold text-red-600">
                        ${jobDetail.calls.reduce((sum, call) => sum + (call.provider_cost_usd ?? call.cost_usd ?? 0), 0).toFixed(6)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Your cost to LiteLLM/OpenAI/Anthropic
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">Client Cost (What THEY Pay)</div>
                      <div className="text-2xl font-bold text-green-600">
                        ${jobDetail.calls.reduce((sum, call) => sum + (call.client_cost_usd ?? call.cost_usd ?? 0), 0).toFixed(6)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        What you charge your client (with markup)
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">Your Profit</div>
                      <div className="text-2xl font-bold text-blue-600">
                        ${(jobDetail.calls.reduce((sum, call) => sum + (call.client_cost_usd ?? call.cost_usd ?? 0), 0) -
                            jobDetail.calls.reduce((sum, call) => sum + (call.provider_cost_usd ?? call.cost_usd ?? 0), 0)).toFixed(6)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {jobDetail.calls.reduce((sum, call) => sum + (call.provider_cost_usd ?? call.cost_usd ?? 0), 0) > 0
                          ? `${(((jobDetail.calls.reduce((sum, call) => sum + (call.client_cost_usd ?? call.cost_usd ?? 0), 0) -
                                jobDetail.calls.reduce((sum, call) => sum + (call.provider_cost_usd ?? call.cost_usd ?? 0), 0)) /
                                jobDetail.calls.reduce((sum, call) => sum + (call.provider_cost_usd ?? call.cost_usd ?? 0), 0)) * 100).toFixed(1)}% profit margin`
                          : 'N/A'}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* LLM Calls Card */}
              <Card>
                <CardHeader>
                  <CardTitle>LLM Calls</CardTitle>
                  <CardDescription>
                    {jobDetail.calls.length} calls made during job execution
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {jobDetail.calls.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      No LLM calls recorded for this job.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Call ID</TableHead>
                            <TableHead>Model</TableHead>
                            <TableHead>Purpose</TableHead>
                            <TableHead>Time</TableHead>
                            <TableHead className="text-right">Tokens</TableHead>
                            <TableHead className="text-right">Provider Cost (YOU Pay)</TableHead>
                            <TableHead className="text-right">Client Cost (THEY Pay)</TableHead>
                            <TableHead className="text-right">Your Profit</TableHead>
                            <TableHead className="text-right">Latency</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {jobDetail.calls.map((call) => (
                            <>
                              <TableRow key={call.call_id}>
                                <TableCell className="font-mono text-xs">
                                  {call.call_id.substring(0, 8)}...
                                </TableCell>
                                <TableCell>
                                  <div className="text-sm font-medium">
                                    {call.resolved_model || call.model_used || 'N/A'}
                                  </div>
                                  {call.model_group_used && (
                                    <div className="text-xs text-muted-foreground">
                                      Alias: {call.model_group_used}
                                    </div>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {call.purpose ? (
                                    <Badge variant="outline">{call.purpose}</Badge>
                                  ) : (
                                    <span className="text-muted-foreground">-</span>
                                  )}
                                </TableCell>
                                <TableCell className="text-sm">
                                  {new Date(call.created_at).toLocaleTimeString()}
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="text-sm">
                                    {call.total_tokens.toLocaleString()}
                                  </div>
                                  <div className="text-xs text-muted-foreground">
                                    {call.prompt_tokens.toLocaleString()} in / {call.completion_tokens.toLocaleString()} out
                                  </div>
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="text-sm font-medium text-red-600">
                                    ${(call.provider_cost_usd ?? call.cost_usd ?? 0).toFixed(6)}
                                  </div>
                                  {call.model_pricing_input !== null && call.model_pricing_output !== null && (
                                    <div className="text-xs text-muted-foreground">
                                      ${call.model_pricing_input}/M in • ${call.model_pricing_output}/M out
                                    </div>
                                  )}
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="text-sm font-medium text-green-600">
                                    ${(call.client_cost_usd ?? call.cost_usd ?? 0).toFixed(6)}
                                  </div>
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="text-sm font-medium text-blue-600">
                                    ${((call.client_cost_usd ?? call.cost_usd ?? 0) - (call.provider_cost_usd ?? call.cost_usd ?? 0)).toFixed(6)}
                                  </div>
                                  {(call.provider_cost_usd ?? call.cost_usd ?? 0) > 0 && (
                                    <div className="text-xs text-muted-foreground">
                                      {((((call.client_cost_usd ?? call.cost_usd ?? 0) - (call.provider_cost_usd ?? call.cost_usd ?? 0)) / (call.provider_cost_usd ?? call.cost_usd ?? 1)) * 100).toFixed(1)}% markup
                                    </div>
                                  )}
                                </TableCell>
                                <TableCell className="text-right">
                                  {call.latency_ms ? `${call.latency_ms}ms` : '-'}
                                </TableCell>
                                <TableCell>
                                  {call.error ? (
                                    <Badge variant="destructive">Error</Badge>
                                  ) : (
                                    <Badge variant="default">Success</Badge>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => toggleCallExpansion(call.call_id)}
                                  >
                                    {expandedCall === call.call_id ? 'Hide' : 'Show'} Details
                                  </Button>
                                </TableCell>
                              </TableRow>
                              {expandedCall === call.call_id && (
                                <TableRow>
                                  <TableCell colSpan={11} className="bg-muted/30">
                                    <div className="p-4 space-y-4">
                                      {call.error && (
                                        <div>
                                          <div className="text-sm font-medium text-destructive mb-2">
                                            Error
                                          </div>
                                          <pre className="bg-destructive/10 p-3 rounded text-xs overflow-x-auto border border-destructive/20">
                                            {call.error}
                                          </pre>
                                        </div>
                                      )}

                                      {call.request_data && (
                                        <div>
                                          <div className="text-sm font-medium mb-2">
                                            Request Data
                                          </div>
                                          <pre className="bg-muted/50 p-3 rounded text-xs overflow-x-auto border">
                                            {JSON.stringify(call.request_data, null, 2)}
                                          </pre>
                                        </div>
                                      )}

                                      {call.response_data && (
                                        <div>
                                          <div className="text-sm font-medium mb-2">
                                            Response Data
                                          </div>
                                          <pre className="bg-muted/50 p-3 rounded text-xs overflow-x-auto border">
                                            {JSON.stringify(call.response_data, null, 2)}
                                          </pre>
                                        </div>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              )}
                            </>
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
              Job not found.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
