export interface User {
  id: string
  username: string
  role: 'owner' | 'user'
}

export interface Organization {
  organization_id: string
  name: string
  status: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Team {
  team_id: string
  organization_id: string
  team_alias?: string
  virtual_key: string
  model_groups: string[]  // Deprecated - use access_groups
  access_groups: string[]
  allowed_model_aliases?: string[]
  credits: {
    credits_allocated: number
    credits_used: number
    credits_remaining: number
  }
  credits_allocated?: number
  credits_remaining?: number
  credits_used?: number
  budget_mode?: 'job_based' | 'consumption_usd' | 'consumption_tokens'
  credits_per_dollar?: number
  status?: 'active' | 'suspended' | 'paused'
  created_at?: string
}

export interface ModelGroup {
  model_group_id: string
  group_name: string
  display_name: string
  description?: string
  status: string
  models: Array<{
    model_name: string
    priority: number
  }>
}

// New model alias types
export interface ModelAlias {
  model_alias: string
  display_name: string
  provider: string
  actual_model: string
  litellm_model_id?: string
  access_groups: string[]
  description?: string
  pricing_input?: number
  pricing_output?: number
  status: string
  teams_using?: string[]
  created_at: string
  updated_at: string
}

export interface ModelAccessGroup {
  group_name: string
  display_name: string
  description?: string
  status: string
  model_aliases: Array<{
    model_alias: string
    display_name: string
    provider: string
    actual_model: string
  }>
  teams_using?: string[]
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: string
  timestamp: string
  user: string
  user_id: string
  action: 'create' | 'update' | 'delete'
  entity_type: 'organization' | 'team' | 'model_group' | 'user'
  entity_id: string
  entity_name: string
  changes?: Record<string, any>
  metadata?: Record<string, any>
}

export interface DashboardStats {
  total_organizations: number
  total_teams: number
  total_credits_allocated: number
  recent_activity: AuditLog[]
}

export interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isAuthenticated: boolean
}
