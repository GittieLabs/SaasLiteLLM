# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-31

### 🚀 Major Changes

#### Direct Provider Integration (Breaking Change)
- **Removed LiteLLM Proxy Layer** - Eliminated port 8002 proxy, now making direct HTTPS calls to provider APIs
- **Direct Provider Calls** - OpenAI, Anthropic, Google Gemini, and Fireworks AI called directly from SaaS API layer
- **Improved Reliability** - Eliminated proxy as a potential point of failure
- **Better Performance** - Reduced latency by removing intermediate hop
- **Simplified Architecture** - Cleaner system with fewer moving parts

### ✨ New Features

#### Provider Credentials Management
- **Organization-Level Credentials** - Store encrypted API keys per organization
- **Multi-Provider Support** - OpenAI, Anthropic, Google Gemini, Fireworks AI
- **Fernet Encryption** - Secure at-rest encryption using MASTER_KEY environment variable
- **Admin UI** - Complete CRUD interface for managing provider credentials
- **API Endpoints** - Full REST API for credential management
- **Active/Inactive Status** - Enable/disable credentials without deletion
- **Custom API Base URLs** - Support for custom endpoints and proxies

#### Model Pricing Overview
- **40+ Model Catalog** - GPT-5, Claude Opus 4.1, Gemini 2.5, DeepSeek R1, and more
- **Multi-Provider Pricing** - Centralized pricing view across all providers
- **Cost Comparisons** - Built-in cost comparison examples
- **Search & Filter** - Find models by name or provider
- **Context Window Info** - Maximum token capacity for each model
- **Auto-Pricing Integration** - Model aliases auto-populate pricing from catalog

#### Cost Transparency System
- **Dual Cost Tracking** - Separate provider cost vs client cost
- **Markup Configuration** - Configurable markup percentage per team
- **Profit Visibility** - Real-time profit margin tracking
- **Budget Modes** - Job-based, consumption (USD), consumption (tokens)
- **Detailed Cost Breakdown** - Input cost, output cost, markup applied
- **Per-Call Cost Tracking** - Every LLM call tracks both costs

#### Authentication System
- **JWT-Based Auth** - Secure token-based authentication for admin dashboard
- **Role-Based Access** - Owner, Admin, Viewer roles with granular permissions
- **Initial Setup Flow** - One-time setup endpoint for first admin user
- **Password Management** - Change password, admin-initiated resets
- **Session Management** - Configurable token expiration (default 24 hours)
- **Security Best Practices** - Documented password requirements and account security

### 🔧 Enhancements

#### Database Schema
- **New provider_credentials Table** - Stores encrypted provider API keys
- **Enhanced llm_calls Table** - Added 6 new cost tracking fields:
  - `input_cost_usd`, `output_cost_usd` - Separate input/output costs
  - `provider_cost_usd`, `client_cost_usd` - Dual cost tracking
  - `model_pricing_input`, `model_pricing_output` - Pricing at call time
- **Extended team_credits Table** - Added 5 cost transparency fields:
  - `cost_markup_percentage` - Markup for profit tracking
  - `budget_mode` - Budget mode selection
  - `credits_per_dollar`, `tokens_per_credit` - Conversion rates
  - `status` - Team status field

#### Model Aliases
- **Direct Provider Integration** - Model aliases resolve to actual provider models without LiteLLM proxy
- **Auto-Pricing from Catalog** - Pricing auto-populated from llm_pricing_current.json
- **Access Control** - Model aliases can be restricted to specific access groups
- **40+ Models Supported** - Full catalog of latest models from all providers

#### Admin Dashboard
- **Provider Credentials Page** - New page for managing API keys
- **Model Pricing Page** - New page displaying model catalog and pricing
- **Authentication Page** - Login/logout flow with JWT tokens
- **Cost Transparency Views** - Enhanced team pages with profit margin visibility
- **Improved Navigation** - Reorganized sidebar with new sections

### 📚 Documentation

#### New Documentation Pages
- **Provider Credentials Admin Guide** - Complete guide for managing credentials via UI
- **Provider Credentials API Reference** - REST API documentation with examples
- **Model Pricing Guide** - Model catalog, pricing comparisons, cost calculator
- **Authentication Guide** - JWT authentication, roles, password management
- **Cost Transparency Guide** - Dual cost tracking, markup configuration
- **Model Aliases API Reference** - Updated for direct provider integration

#### Updated Documentation
- **Architecture Documentation** - Completely rewritten to remove LiteLLM proxy references
- **Database Schema Reference** - Added new tables and fields
- **Getting Started Guide** - Updated for v1.0.0 architecture
- **mkdocs Navigation** - Reorganized with new pages in proper sections

### 🐛 Bug Fixes

#### Streaming Fixes
- **Async Context Manager Fix** - Removed async context manager from httpx.Response streaming
- **Streaming Reliability** - Fixed async iteration issues in streaming endpoints
- **Diagnostic Logging** - Added comprehensive logging for debugging streaming issues

#### Model Resolution
- **Model Alias Resolution** - Fixed resolution of model aliases to actual provider models
- **Provider Selection** - Improved provider selection logic based on model aliases

### 🔒 Security

- **Encrypted Credentials** - Provider API keys encrypted at rest using Fernet
- **JWT Authentication** - Secure token-based authentication for admin access
- **Role-Based Permissions** - Granular access control (owner, admin, viewer)
- **Password Hashing** - Secure password storage for admin users
- **HTTPS Direct Calls** - All provider API calls use secure HTTPS

### ⚡ Performance

- **Reduced Latency** - Eliminated LiteLLM proxy hop for faster API calls
- **Direct Provider Calls** - No intermediate proxy layer
- **Optimized Database Queries** - Improved indexes for cost tracking queries

### 🗑️ Deprecated

- **LiteLLM Proxy** - No longer used (removed port 8002)
- **Legacy Cost Field** - `llm_calls.cost_usd` deprecated in favor of separate input/output costs

### 📦 Admin Panel [1.3.0]

- **Provider Credentials UI** - Complete CRUD interface for managing API keys
- **Model Pricing Page** - Interactive model catalog with search and filtering
- **Authentication Flow** - Login page, JWT token management, logout
- **Cost Transparency UI** - Enhanced team pages showing profit margins
- **Improved Layouts** - Better organization and navigation

### 🛠️ Migration Guide

#### Breaking Changes

1. **LiteLLM Proxy Removed**
   - Update any direct references to port 8002
   - Provider calls now go directly to OpenAI, Anthropic, etc.
   - Model aliases resolve to actual provider models

2. **Database Schema Changes**
   - Run migration to add `provider_credentials` table
   - Run migration to add new cost tracking fields to `llm_calls`
   - Run migration to add cost transparency fields to `team_credits`

3. **Environment Variables**
   - Add `MASTER_KEY` for provider credential encryption
   - Add `JWT_SECRET_KEY` for admin authentication
   - Add `JWT_EXPIRATION_HOURS` (optional, default 24)

#### Migration Steps

1. **Backup Database**
   ```bash
   pg_dump -U postgres saas_litellm > backup_pre_v1.0.0.sql
   ```

2. **Update Environment Variables**
   ```bash
   # Add to .env or Railway environment
   MASTER_KEY=your-32-byte-base64-encoded-key
   JWT_SECRET_KEY=your-jwt-secret-key
   JWT_EXPIRATION_HOURS=24
   ```

3. **Run Database Migrations**
   ```bash
   # Add provider_credentials table
   psql -U postgres -d saas_litellm -f scripts/migrations/008_add_provider_credentials.sql

   # Add cost tracking fields
   psql -U postgres -d saas_litellm -f scripts/migrations/009_add_cost_tracking.sql
   ```

4. **Create Initial Admin User**
   - Navigate to admin dashboard
   - Complete initial setup form
   - First user automatically becomes "owner"

5. **Add Provider Credentials**
   - Log in to admin dashboard
   - Navigate to Provider Credentials
   - Add API keys for OpenAI, Anthropic, etc.

6. **Update Model Aliases**
   - Review existing model aliases
   - Ensure they map to actual provider models
   - Update pricing from catalog if needed

### 📝 Notes

- This is a **major version** release with breaking changes
- LiteLLM proxy has been completely removed from the architecture
- All systems now use direct provider integration
- Comprehensive documentation has been updated to reflect v1.0.0 architecture
- Admin dashboard version bumped to v1.3.0 for new features

### 🔗 Links

- [Full Documentation](docs-service/)
- [Architecture Guide](docs-service/docs/getting-started/architecture.md)
- [Migration Guide](docs-service/docs/getting-started/migration-v1.0.md)
- [Provider Credentials](docs-service/docs/admin-dashboard/provider-credentials.md)
- [Model Pricing](docs-service/docs/admin-dashboard/pricing.md)

---

## [0.2.0] - 2024-10-15

### Added
- Credit system with job-based billing
- Model groups and access control
- Team usage summaries
- Webhook registrations
- Basic admin dashboard

### Changed
- Improved database schema with indexes
- Enhanced error handling

### Fixed
- Credit deduction logic
- Model group resolution

---

## [0.1.0] - 2024-09-01

### Added
- Initial release
- Job tracking system
- LLM call logging
- Organization and team management
- Basic credit allocation
- PostgreSQL database schema
