const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

async function request(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
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
};
