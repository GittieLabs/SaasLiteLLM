# Provider Credentials

Manage encrypted LLM provider API keys at the organization level for secure, direct provider integration.

## Overview

Provider Credentials allows administrators to securely store and manage API keys for LLM providers (OpenAI, Anthropic, Google Gemini, Fireworks AI) at the organization level. All credentials are encrypted at rest and can be activated/deactivated without deletion.

!!! info "New in v1.0.0"
    Provider credentials management was introduced in version 1.0.0 with the move to direct provider integration. This replaces the previous LiteLLM proxy configuration.

## Key Features

- **Encrypted Storage** - API keys encrypted using Fernet symmetric encryption
- **Organization-Level** - Each organization can have its own provider credentials
- **Multi-Provider Support** - OpenAI, Anthropic, Gemini, Fireworks AI
- **Multiple Credentials** - Multiple API keys per provider for rotation
- **Activate/Deactivate** - Temporarily disable credentials without deletion
- **Fallback to Environment** - Falls back to environment variables if no org credentials exist
- **Audit Trail** - Track creation and update timestamps

## Accessing Provider Credentials

Navigate to **Provider Credentials** from the sidebar in the Admin Dashboard.

![Provider Credentials Page](../assets/screenshots/provider-credentials.png)

## Supported Providers

| Provider | API Key Format | Get API Key |
|----------|---------------|-------------|
| **OpenAI** | `sk-...` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Anthropic** | `sk-ant-...` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| **Google Gemini** | `AI...` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| **Fireworks AI** | `fw...` | [fireworks.ai/account/api-keys](https://fireworks.ai/account/api-keys) |

## Creating a Credential

1. Click **"Add Provider Credential"**
2. Fill in the form:
   - **Organization** - Select the organization (required)
   - **Provider** - Choose provider (OpenAI, Anthropic, Gemini, Fireworks)
   - **Credential Name** - Descriptive name (e.g., "Production OpenAI Key")
   - **API Key** - The provider's API key (will be encrypted)
   - **API Base URL** - Optional custom endpoint (for proxy setups)
3. Click **"Create Credential"**

The API key is immediately encrypted before storage and never displayed again.

## Editing a Credential

1. Click the **Edit** button next to the credential
2. Update the fields:
   - **Credential Name** - Change the descriptive name
   - **API Key** - Provide a new API key if rotating
   - **API Base URL** - Update custom endpoint
3. Click **"Update"**

!!! warning "API Key Update"
    When updating the API key field, you must provide the full new key. The existing encrypted key is never displayed for security reasons.

## Activating/Deactivating Credentials

**Activate:**
- Click the **Activate** button
- The credential becomes available for LLM API calls
- Status changes to "Active" (green badge)

**Deactivate:**
- Click the **Deactivate** button
- The credential is temporarily disabled
- Status changes to "Inactive" (gray badge)
- Useful for rotating keys or troubleshooting

## Deleting a Credential

1. Click the **Delete** button next to the credential
2. Confirm the deletion in the dialog
3. The credential is permanently removed from the database

!!! danger "Permanent Deletion"
    Deleting a credential is permanent and cannot be undone. If teams are using this credential, their API calls will fail. Consider deactivating instead of deleting for temporary issues.

## How Credentials Are Used

### Priority Order

When making an LLM API call, the system looks for provider credentials in this order:

1. **Organization's Active Credentials** - Checks for active credentials for the team's organization
2. **Environment Variables** - Falls back to `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
3. **Error** - If neither exists, the API call fails with authentication error

### Example Flow

```
Team makes API call
  ↓
System checks team's organization
  ↓
Looks for active provider credentials
  ↓
If found: Use organization's encrypted key
If not found: Use environment variable
  ↓
Make direct API call to provider
```

## Security Considerations

### Encryption

- **Algorithm** - Fernet symmetric encryption (AES-128-CBC with HMAC)
- **Key Storage** - Encryption key stored in `MASTER_KEY` environment variable
- **At Rest** - All API keys encrypted in PostgreSQL database
- **In Transit** - HTTPS for all API communications

### Access Control

- **Admin Only** - Only administrators with dashboard access can view/edit credentials
- **Never Exposed** - Encrypted API keys never returned via API responses
- **Organization Isolation** - Each organization's credentials are separate
- **Audit Logging** - Creation and update timestamps tracked

### Best Practices

✅ **DO:**
- Use separate API keys for production and development
- Rotate API keys regularly (every 90 days recommended)
- Deactivate unused credentials
- Use descriptive names for easy identification
- Monitor usage to detect unauthorized access

❌ **DON'T:**
- Share API keys between organizations
- Store unencrypted keys in code or config files
- Use personal API keys for production workloads
- Delete credentials while teams are actively using them

## Troubleshooting

### API Calls Failing with Authentication Error

**Cause:** No active credentials for the provider

**Solution:**
1. Check if organization has an active credential for the provider
2. Verify the credential is marked as "Active"
3. Test the API key directly with the provider's API
4. Check environment variables as fallback

### Credential Not Showing in List

**Cause:** Filtered by organization or provider

**Solution:**
1. Check organization filter at top of page
2. Verify you're viewing the correct organization
3. Check if credential was deleted

### Cannot Update API Key

**Cause:** API key field validation failed

**Solution:**
1. Verify API key format matches provider requirements
2. Copy/paste key carefully (no extra spaces)
3. Check key is valid by testing with provider's API

## API Endpoints

Provider credentials can also be managed via API:

### List Credentials for Organization
```http
GET /api/provider-credentials/organization/{organization_id}
```

### Create Credential
```http
POST /api/provider-credentials/create
Content-Type: application/json

{
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production Key",
  "api_key": "sk-...",
  "api_base": null
}
```

### Update Credential
```http
PUT /api/provider-credentials/{credential_id}
Content-Type: application/json

{
  "credential_name": "Updated Name",
  "api_key": "sk-new-key..."
}
```

### Activate Credential
```http
PUT /api/provider-credentials/{credential_id}/activate
```

### Deactivate Credential
```http
PUT /api/provider-credentials/{credential_id}/deactivate
```

### Delete Credential
```http
DELETE /api/provider-credentials/{credential_id}
```

[:octicons-arrow-right-24: See API Reference](../api-reference/provider-credentials.md)

## Related Pages

- **[Model Aliases](model-aliases.md)** - Configure which models teams can use
- **[Model Pricing](pricing.md)** - View pricing for all provider models
- **[Architecture](../getting-started/architecture.md)** - Understand provider integration
- **[Cost Transparency](cost-transparency.md)** - Track provider vs client costs
