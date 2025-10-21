const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

// Get authentication token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  // Prefer JWT token (new auth system)
  const jwtToken = localStorage.getItem('jwtToken');
  if (jwtToken) return jwtToken;
  // Fallback to legacy admin key for backward compatibility
  return localStorage.getItem('adminKey');
}

async function request(endpoint: string, options: RequestInit = {}) {
  const authToken = getAuthToken();

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));

    // If unauthorized, clear stored credentials and redirect to login
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('jwtToken');
      localStorage.removeItem('adminKey');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

export const api = {
  // Dashboard
  getDashboardStats: () => request('/api/stats/dashboard'),

  // Organizations
  getOrganizations: () => request('/api/organizations'),
  getOrganization: (id: string) => request(`/api/organizations/${id}`),
  createOrganization: (data: any) => request('/api/organizations/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Teams
  getTeams: () => request('/api/teams'),
  getTeam: (id: string) => request(`/api/teams/${id}`),
  createTeam: (data: any) => request('/api/teams/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateTeam: (teamId: string, data: any) => request(`/api/teams/${teamId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  deleteTeam: (teamId: string) => request(`/api/teams/${teamId}`, {
    method: 'DELETE',
  }),
  suspendTeam: (teamId: string) => request(`/api/teams/${teamId}/suspend`, {
    method: 'PUT',
  }),
  resumeTeam: (teamId: string) => request(`/api/teams/${teamId}/resume`, {
    method: 'PUT',
  }),

  // Model Groups (deprecated - use Model Aliases)
  getModelGroups: () => request('/api/model-groups'),
  createModelGroup: (data: any) => request('/api/model-groups/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Model Aliases
  getModelAliases: () => request('/api/models'),
  getModelAlias: (alias: string) => request(`/api/models/${alias}`),
  createModelAlias: (data: any) => request('/api/models/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateModelAlias: (alias: string, data: any) => request(`/api/models/${alias}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  deleteModelAlias: (alias: string) => request(`/api/models/${alias}`, {
    method: 'DELETE',
  }),

  // Model Access Groups
  getModelAccessGroups: () => request('/api/model-access-groups'),
  getModelAccessGroup: (groupName: string) => request(`/api/model-access-groups/${groupName}`),
  createModelAccessGroup: (data: any) => request('/api/model-access-groups/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateModelAccessGroup: (groupName: string, data: any) => request(`/api/model-access-groups/${groupName}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  updateModelAccessGroupModels: (groupName: string, modelAliases: string[]) => request(`/api/model-access-groups/${groupName}/models`, {
    method: 'PUT',
    body: JSON.stringify({ model_aliases: modelAliases }),
  }),
  deleteModelAccessGroup: (groupName: string) => request(`/api/model-access-groups/${groupName}`, {
    method: 'DELETE',
  }),

  // Credits
  getCredits: (teamId: string) => request(`/api/credits/teams/${teamId}/balance`),

  // Admin Users
  getAdminUsers: () => request('/api/admin-users'),
  getAdminUser: (userId: string) => request(`/api/admin-users/${userId}`),
  createAdminUser: (data: any) => request('/api/admin-users', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateAdminUser: (userId: string, data: any) => request(`/api/admin-users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  deleteAdminUser: (userId: string) => request(`/api/admin-users/${userId}`, {
    method: 'DELETE',
  }),
  getAuditLogs: (params?: any) => {
    const queryParams = new URLSearchParams(params).toString();
    return request(`/api/admin-users/audit-logs${queryParams ? `?${queryParams}` : ''}`);
  },

  // Jobs
  getTeamJobs: (teamId: string, params?: any) => {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    return request(`/api/jobs/teams/${teamId}${queryParams ? `?${queryParams}` : ''}`);
  },
  getJobDetail: (teamId: string, jobId: string) => {
    return request(`/api/jobs/teams/${teamId}/${jobId}`);
  },
  getOrganizationJobStats: (organizationId: string, params?: any) => {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    return request(`/api/jobs/organizations/${organizationId}/stats${queryParams ? `?${queryParams}` : ''}`);
  },
  getOrganizationAnalytics: (organizationId: string, params?: any) => {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    return request(`/api/jobs/organizations/${organizationId}/analytics${queryParams ? `?${queryParams}` : ''}`);
  },
};
