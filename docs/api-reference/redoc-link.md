# Full API Documentation

For complete, interactive API documentation, use the auto-generated API docs provided by the SaaS API.

## Interactive API Documentation

### ReDoc (Recommended)

**Beautiful, responsive API documentation with examples**

[:octicons-link-external-24: Open ReDoc Documentation (Production)](https://llm-saas.usegittie.com/redoc){ .md-button .md-button--primary }

[:octicons-link-external-24: Open ReDoc Documentation (Local)](http://localhost:8003/redoc){ .md-button }

ReDoc provides:
- ✅ Clean, professional interface
- ✅ Comprehensive endpoint documentation
- ✅ Request/response schemas
- ✅ Example payloads
- ✅ Model definitions
- ✅ Authentication details
- ✅ Mobile-friendly

**URL:** `http://localhost:8003/redoc`

---

### Swagger UI

**Interactive API explorer with "Try it out" functionality**

[:octicons-link-external-24: Open Swagger UI (Production)](https://llm-saas.usegittie.com/docs){ .md-button }

[:octicons-link-external-24: Open Swagger UI (Local)](http://localhost:8003/docs){ .md-button }

Swagger UI provides:
- ✅ Try API calls directly in the browser
- ✅ Interactive request builder
- ✅ Real-time response preview
- ✅ Schema validation
- ✅ Authentication testing
- ✅ Download OpenAPI spec

**URL:** `http://localhost:8003/docs`

---

## What's Available

Both interfaces provide complete documentation for:

### Organizations API
- Create, read, update, delete organizations
- List organization teams
- Get organization usage statistics

### Teams API
- Create, read, update, delete teams
- Manage model access groups
- Suspend/resume teams
- View team credits

### Model Access Groups API
- Create and manage access groups
- Assign model aliases
- Control team access

### Model Aliases API
- Create model aliases
- Configure pricing (input/output tokens)
- Provider configuration

### Jobs API
- Create jobs
- Single-call job endpoints (streaming and non-streaming)
  - `POST /api/jobs/create-and-call` - Non-streaming single-call
  - `POST /api/jobs/create-and-call-stream` - **Streaming single-call (SSE)**
- Make LLM calls within jobs
- Complete jobs
- Get job details and costs

### Credits API
- Check credit balance
- Add credits
- View credit transactions
- Credit availability check

### Health & Status
- Health check endpoint
- System status

---

## Quick Access

<div class="grid cards" markdown>

-   **:material-api: ReDoc**

    ---

    Beautiful, responsive documentation

    [:octicons-arrow-right-24: Production](https://llm-saas.usegittie.com/redoc) | [:octicons-arrow-right-24: Local](http://localhost:8003/redoc)

-   **:material-test-tube: Swagger UI**

    ---

    Interactive API testing interface

    [:octicons-arrow-right-24: Production](https://llm-saas.usegittie.com/docs) | [:octicons-arrow-right-24: Local](http://localhost:8003/docs)

-   **:material-code-json: OpenAPI Spec**

    ---

    Download OpenAPI 3.0 specification

    [:octicons-arrow-right-24: Production](https://llm-saas.usegittie.com/openapi.json) | [:octicons-arrow-right-24: Local](http://localhost:8003/openapi.json)

</div>

---

## Using the Interactive Docs

### ReDoc Interface

1. **Browse endpoints** - Navigate through the API structure
2. **View schemas** - See request/response models
3. **Copy examples** - Use example code in your app
4. **Search** - Find specific endpoints quickly

### Swagger UI Interface

1. **Select an endpoint** - Click on any API endpoint
2. **Click "Try it out"** - Enable interactive mode
3. **Fill parameters** - Add your virtual key and request data
4. **Execute** - Send the request and see live results

!!! tip "Authentication in Swagger UI"
    To test authenticated endpoints in Swagger UI:

    1. Click the **"Authorize"** button at the top
    2. Enter your virtual key: `Bearer sk-your-virtual-key`
    3. Click **"Authorize"**
    4. Now all requests will include authentication

---

## OpenAPI Specification

Download the OpenAPI 3.0 specification to:
- Generate client libraries
- Import into API testing tools (Postman, Insomnia)
- Build custom tooling
- Integrate with CI/CD

```bash
# Download OpenAPI spec
curl http://localhost:8003/openapi.json > saas-api-spec.json
```

---

## Production URLs

When deploying to production, the API documentation will be available at:

| Environment | ReDoc | Swagger UI | OpenAPI Spec |
|-------------|-------|------------|--------------|
| **Production** | https://llm-saas.usegittie.com/redoc | https://llm-saas.usegittie.com/docs | https://llm-saas.usegittie.com/openapi.json |
| **Local** | http://localhost:8003/redoc | http://localhost:8003/docs | http://localhost:8003/openapi.json |

---

## Additional API Resources

Beyond the interactive documentation, explore these resources:

### Detailed Guides

- **[API Overview](overview.md)** - Introduction to the API structure
- **[Jobs API](jobs.md)** - Job management endpoints
- **[LLM Calls API](llm-calls.md)** - Making LLM calls
- **[Teams API](teams.md)** - Team management
- **[Organizations API](organizations.md)** - Organization management

### Integration Guides

- **[Integration Overview](../integration/overview.md)** - How to integrate
- **[Authentication](../integration/authentication.md)** - Virtual key auth
- **[Job Workflow](../integration/job-workflow.md)** - Job-based pattern
- **[Streaming](../integration/streaming.md)** - SSE streaming guide

### Examples

- **[Basic Usage](../examples/basic-usage.md)** - Simple examples
- **[Streaming Examples](../examples/streaming-examples.md)** - Real-time streaming
- **[Full Chain](../examples/full-chain.md)** - Complete workflow

---

## Getting Help

If you have questions about the API:

1. **Check the interactive docs** - Most questions are answered there
2. **Review the integration guides** - Detailed explanations and examples
3. **Try the examples** - Working code you can run locally

---

## Screenshots

### ReDoc Interface

![ReDoc Screenshot](https://raw.githubusercontent.com/Redocly/redoc/master/docs/images/redoc-demo.png)

*Clean, professional API documentation with ReDoc*

### Swagger UI Interface

![Swagger UI Screenshot](https://static1.smartbear.co/swagger/media/images/swagger-ui-screenshot.png)

*Interactive API testing with Swagger UI*

---

!!! success "Ready to Explore"
    Open the interactive documentation and start exploring the API:

    - **[ReDoc](http://localhost:8003/redoc)** - Beautiful documentation
    - **[Swagger UI](http://localhost:8003/docs)** - Interactive testing
