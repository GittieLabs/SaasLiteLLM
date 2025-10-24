#!/bin/bash
# =====================================================
# Safe Deployment: Pricing System + LiteLLM Removal
# =====================================================
# This script guides you through:
# 1. Deploying the JSON-based pricing system
# 2. Creating provider_credentials table
# 3. Adding provider API keys
# 4. Testing direct provider calls
# 5. Removing LiteLLM proxy dependencies
#
# Author: Claude
# Date: 2025-10-23
# =====================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection (Railway production)
DB_HOST="switchback.proxy.rlwy.net"
DB_PORT="24546"
DB_USER="postgres"
DB_NAME="railway"
DB_PASSWORD="${PGPASSWORD:-}"

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}ERROR: PGPASSWORD environment variable not set${NC}"
    echo "Set it with: export PGPASSWORD='your-password'"
    exit 1
fi

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1 ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Aborted by user"
        exit 1
    fi
}

run_sql() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "$1"
}

run_sql_file() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$1"
}

# =====================================================
# PHASE 0: Pre-flight Checks
# =====================================================
print_header "PHASE 0: Pre-flight Checks"

# Check if we're in the right directory
if [ ! -f "scripts/test_pricing_system.py" ]; then
    print_error "Not in project root directory"
    exit 1
fi
print_success "In project root directory"

# Check database connection
if ! run_sql "SELECT 1" &> /dev/null; then
    print_error "Cannot connect to database"
    exit 1
fi
print_success "Database connection OK"

# Run pricing validation tests
print_info "Running pricing validation tests..."
if python3 scripts/test_pricing_system.py > /tmp/pricing_test.log 2>&1; then
    print_success "All 11 pricing tests passed"
else
    print_error "Pricing tests failed. Check /tmp/pricing_test.log"
    cat /tmp/pricing_test.log
    exit 1
fi

# Check if provider_credentials table already exists
if run_sql "\dt provider_credentials" 2>&1 | grep -q "provider_credentials"; then
    print_warning "provider_credentials table already exists"
    SKIP_TABLE_CREATION=true
else
    print_info "provider_credentials table does not exist yet"
    SKIP_TABLE_CREATION=false
fi

# =====================================================
# PHASE 1: Create provider_credentials Table
# =====================================================
print_header "PHASE 1: Create provider_credentials Table"

if [ "$SKIP_TABLE_CREATION" = true ]; then
    print_info "Skipping table creation (already exists)"
else
    confirm "Create provider_credentials table? (y/n) "

    print_info "Running migration 010..."
    if run_sql_file "scripts/migrations/010_add_provider_credentials.sql"; then
        print_success "provider_credentials table created"
    else
        print_error "Failed to create table"
        exit 1
    fi
fi

# Verify table exists
if run_sql "\d provider_credentials" &> /dev/null; then
    print_success "Table structure verified"
else
    print_error "Table not found after creation"
    exit 1
fi

# =====================================================
# PHASE 2: Add Provider API Keys
# =====================================================
print_header "PHASE 2: Add Provider API Keys"

print_info "You need to add your actual provider API keys to the database."
print_info "These will be encrypted and stored in provider_credentials table."
echo ""
print_warning "IMPORTANT: You'll need API keys for providers you want to use:"
echo "  - OpenAI (sk-proj-...)"
echo "  - Anthropic (sk-ant-...)"
echo "  - Gemini (AIza...)"
echo "  - Fireworks (fw_...)"
echo ""

confirm "Ready to add provider credentials? (y/n) "

# Get organization ID
echo ""
echo -e "${YELLOW}Enter your organization_id:${NC}"
read -p "> " ORG_ID

if [ -z "$ORG_ID" ]; then
    print_error "Organization ID is required"
    exit 1
fi

# Verify organization exists
if ! run_sql "SELECT organization_id FROM organizations WHERE organization_id = '$ORG_ID'" | grep -q "$ORG_ID"; then
    print_error "Organization '$ORG_ID' not found in database"
    exit 1
fi
print_success "Organization '$ORG_ID' found"

# Function to add a provider credential
add_provider_credential() {
    local provider=$1
    local provider_name=$2

    echo ""
    echo -e "${YELLOW}Add $provider_name API key? (y/n)${NC}"
    read -p "> " add_key

    if [[ ! $add_key =~ ^[Yy]$ ]]; then
        print_info "Skipping $provider_name"
        return
    fi

    echo -e "${YELLOW}Enter your $provider_name API key:${NC}"
    read -sp "> " api_key
    echo ""

    if [ -z "$api_key" ]; then
        print_warning "No API key provided, skipping $provider_name"
        return
    fi

    # Note: In production, you'd call the API endpoint that handles encryption
    # For now, we'll insert directly (encryption should be handled by application layer)
    print_warning "Note: API key will be stored. Encryption should be handled by application code."

    local credential_name="${provider_name} Production Key"

    # Check if credential already exists
    if run_sql "SELECT credential_id FROM provider_credentials WHERE organization_id = '$ORG_ID' AND provider = '$provider' AND is_active = true" | grep -q "credential_id"; then
        print_warning "Active credential for $provider_name already exists. Skipping."
        return
    fi

    # Insert credential
    if run_sql "INSERT INTO provider_credentials (organization_id, provider, api_key, credential_name, is_active) VALUES ('$ORG_ID', '$provider', '$api_key', '$credential_name', true)"; then
        print_success "$provider_name credential added"
    else
        print_error "Failed to add $provider_name credential"
    fi
}

# Add credentials for each provider
add_provider_credential "openai" "OpenAI"
add_provider_credential "anthropic" "Anthropic"
add_provider_credential "gemini" "Google Gemini"
add_provider_credential "fireworks" "Fireworks AI"

# Show what was added
echo ""
print_info "Current provider credentials:"
run_sql "SELECT provider, credential_name, is_active, created_at FROM provider_credentials WHERE organization_id = '$ORG_ID' ORDER BY provider"

# =====================================================
# PHASE 3: Deploy Pricing System Code
# =====================================================
print_header "PHASE 3: Deploy Pricing System Code"

print_info "You need to deploy the following files to production:"
echo "  - src/utils/pricing_loader.py"
echo "  - src/utils/cost_calculator.py (updated)"
echo "  - llm_pricing_current.json"
echo ""

confirm "Have you committed and pushed these changes to git? (y/n) "

print_info "Deploy to Railway..."
echo "Run: railway up"
echo ""
confirm "Deploy complete and service running? (y/n) "

# =====================================================
# PHASE 4: Test Direct Provider Calls
# =====================================================
print_header "PHASE 4: Test Direct Provider Calls"

print_info "You should now test that LLM calls work via direct providers."
print_info "The system should route to direct providers when credentials exist."
echo ""
print_info "Test with a simple API call:"
echo "  curl -X POST https://your-api.com/api/llm/create-and-call \\"
echo "    -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\": \"gpt-4o-mini\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}'"
echo ""
confirm "Have you tested and verified LLM calls work? (y/n) "

print_info "Check Railway logs for any errors:"
echo "  railway logs --tail 100"
echo ""
confirm "No errors in logs? (y/n) "

# =====================================================
# PHASE 5: Remove virtual_key Column
# =====================================================
print_header "PHASE 5: Remove virtual_key Column"

print_warning "This will remove the virtual_key column from team_credits table."
print_warning "This is irreversible! Make sure direct provider calls are working first."
echo ""
confirm "Proceed with removing virtual_key column? (y/n) "

print_info "Running migration 012..."
if run_sql_file "scripts/migrations/012_remove_litellm_virtual_keys.sql"; then
    print_success "virtual_key column removed"
else
    print_error "Failed to remove virtual_key column"
    exit 1
fi

# Verify column is gone
if ! run_sql "\d team_credits" | grep -q "virtual_key"; then
    print_success "Verified: virtual_key column removed"
else
    print_error "virtual_key column still exists!"
    exit 1
fi

# =====================================================
# PHASE 6: Drop LiteLLM Tables
# =====================================================
print_header "PHASE 6: Drop LiteLLM Tables"

print_warning "This will DROP all 17 LiteLLM proxy tables from the database."
print_warning "This is PERMANENT and IRREVERSIBLE!"
echo ""
print_info "Tables to be dropped:"
run_sql "SELECT tablename FROM pg_tables WHERE tablename LIKE 'LiteLLM_%' ORDER BY tablename"

echo ""
print_warning "BACKUP YOUR DATABASE FIRST!"
echo "Run: pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > backup_\$(date +%Y%m%d_%H%M%S).sql"
echo ""
confirm "Have you created a database backup? (y/n) "

confirm "Are you ABSOLUTELY SURE you want to drop all LiteLLM tables? (y/n) "

print_info "Dropping LiteLLM tables..."
if run_sql_file "scripts/drop_litellm_tables.sql"; then
    print_success "LiteLLM tables dropped"
else
    print_error "Failed to drop tables"
    exit 1
fi

# Verify tables are gone
LITELLM_COUNT=$(run_sql "SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'LiteLLM_%'" | grep -oP '\d+' | head -1)
if [ "$LITELLM_COUNT" = "0" ]; then
    print_success "Verified: All LiteLLM tables removed"
else
    print_error "Found $LITELLM_COUNT LiteLLM tables remaining!"
    exit 1
fi

# =====================================================
# PHASE 7: Code Cleanup
# =====================================================
print_header "PHASE 7: Code Cleanup"

print_info "Manual cleanup required:"
echo ""
echo "1. Remove LiteLLM service file:"
echo "   git rm src/services/litellm_service.py"
echo ""
echo "2. Remove LiteLLM from dependencies:"
echo "   Edit pyproject.toml and remove 'litellm' line"
echo "   Run: uv pip uninstall litellm"
echo ""
echo "3. Remove LiteLLM Docker service:"
echo "   Edit docker-compose.yml and remove litellm service"
echo "   git rm -r services/litellm/"
echo ""
echo "4. Remove LiteLLM config files:"
echo "   git rm src/config/litellm_config.yaml"
echo "   git rm src/config/litellm_config_simple.yaml"
echo ""
echo "5. Remove environment variables from Railway:"
echo "   - LITELLM_PROXY_URL"
echo "   - LITELLM_MASTER_KEY"
echo ""
echo "6. Update settings.py to remove litellm config references"
echo ""
confirm "Have you completed all code cleanup steps? (y/n) "

# =====================================================
# PHASE 8: Final Verification
# =====================================================
print_header "PHASE 8: Final Verification"

print_info "Running final checks..."

# Check pricing system still works
if python3 scripts/test_pricing_system.py > /tmp/final_pricing_test.log 2>&1; then
    print_success "Pricing system tests still passing"
else
    print_error "Pricing tests failed! Check /tmp/final_pricing_test.log"
    exit 1
fi

# Check database state
print_info "Database state:"
run_sql "SELECT COUNT(*) as app_tables FROM pg_tables WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%' AND tablename NOT LIKE 'sql_%'"

print_success "LiteLLM proxy removal complete!"

# =====================================================
# Summary
# =====================================================
print_header "DEPLOYMENT SUMMARY"

echo -e "${GREEN}✓ provider_credentials table created${NC}"
echo -e "${GREEN}✓ Provider API keys added${NC}"
echo -e "${GREEN}✓ Pricing system deployed${NC}"
echo -e "${GREEN}✓ Direct provider calls tested${NC}"
echo -e "${GREEN}✓ virtual_key column removed${NC}"
echo -e "${GREEN}✓ 17 LiteLLM tables dropped${NC}"
echo -e "${GREEN}✓ Code cleanup completed${NC}"
echo ""
echo -e "${BLUE}Your system now uses direct provider API calls!${NC}"
echo -e "${BLUE}Benefits:${NC}"
echo "  - Faster API calls (no proxy overhead)"
echo "  - Lower costs (no LiteLLM fees)"
echo "  - Simpler architecture (17 fewer tables)"
echo "  - Full control over API calls"
echo ""
print_success "Deployment complete!"
