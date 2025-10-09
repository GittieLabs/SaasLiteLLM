-- Create user if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'litellm_user') THEN
      CREATE USER litellm_user WITH PASSWORD 'litellm_password';
   END IF;
END
$$;

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE litellm TO litellm_user;

-- Connect to litellm database
\c litellm;

-- Grant comprehensive schema privileges
GRANT ALL ON SCHEMA public TO litellm_user;
GRANT CREATE ON SCHEMA public TO litellm_user;
GRANT USAGE ON SCHEMA public TO litellm_user;

-- Grant privileges on existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO litellm_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO litellm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO litellm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO litellm_user;

-- Make litellm_user the owner of the public schema
ALTER SCHEMA public OWNER TO litellm_user;

-- Create extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Basic setup complete
SELECT 'LiteLLM PostgreSQL database initialized successfully!' as message;