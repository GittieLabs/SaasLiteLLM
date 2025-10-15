-- Admin User Management Tables Migration
-- Creates tables for admin dashboard authentication, sessions, and audit logging

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Admin Users Table
-- Stores admin dashboard users with role-based access control
CREATE TABLE IF NOT EXISTS admin_users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'owner', 'admin', 'user'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES admin_users(user_id),
    last_login TIMESTAMP WITH TIME ZONE,
    user_metadata JSONB NOT NULL DEFAULT '{}'
);

-- Indexes for admin_users
CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_role ON admin_users(role);
CREATE INDEX idx_admin_users_is_active ON admin_users(is_active);
CREATE INDEX idx_admin_users_created_at ON admin_users(created_at);

-- Admin Sessions Table
-- Tracks active sessions for JWT token management and revocation
CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES admin_users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE
);

-- Indexes for admin_sessions
CREATE INDEX idx_admin_sessions_user_id ON admin_sessions(user_id);
CREATE INDEX idx_admin_sessions_token_hash ON admin_sessions(token_hash);
CREATE INDEX idx_admin_sessions_expires_at ON admin_sessions(expires_at);
CREATE INDEX idx_admin_sessions_created_at ON admin_sessions(created_at);

-- Admin Audit Log Table
-- Records all admin actions for compliance and security monitoring
CREATE TABLE IF NOT EXISTS admin_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES admin_users(user_id),
    action VARCHAR(100) NOT NULL, -- e.g., 'created_team', 'deleted_user', 'updated_organization'
    resource_type VARCHAR(50), -- e.g., 'team', 'organization', 'user'
    resource_id VARCHAR(255),
    details JSONB, -- Additional context about the action
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for admin_audit_log
CREATE INDEX idx_admin_audit_log_user_id ON admin_audit_log(user_id);
CREATE INDEX idx_admin_audit_log_action ON admin_audit_log(action);
CREATE INDEX idx_admin_audit_log_resource_type ON admin_audit_log(resource_type);
CREATE INDEX idx_admin_audit_log_resource_id ON admin_audit_log(resource_id);
CREATE INDEX idx_admin_audit_log_created_at ON admin_audit_log(created_at);

-- Add comments to tables for documentation
COMMENT ON TABLE admin_users IS 'Admin dashboard users with role-based access control';
COMMENT ON TABLE admin_sessions IS 'Active sessions for JWT token management and revocation';
COMMENT ON TABLE admin_audit_log IS 'Audit trail of all admin actions for compliance and security';

COMMENT ON COLUMN admin_users.role IS 'User role: owner (full access), admin (manage resources), user (read-only)';
COMMENT ON COLUMN admin_users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN admin_sessions.token_hash IS 'SHA-256 hash of JWT token for validation';
COMMENT ON COLUMN admin_audit_log.action IS 'Action performed, e.g., created_team, deleted_user';

-- Verify tables created
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('admin_users', 'admin_sessions', 'admin_audit_log')
ORDER BY tablename;
