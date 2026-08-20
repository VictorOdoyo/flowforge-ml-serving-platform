# API Workflows

## Authentication

Issue a token from `/api/v1/auth/token` using a known user account. The token includes a user ID,
email, and role claims. Protected endpoints require a bearer token.

## Submit a Job

Clients submit work to `/api/v1/jobs` with a job type, priority, input payload, and optional model
version. Use `Idempotency-Key` when a client may retry the same submission after a timeout.

## Poll Job State

Clients can list jobs with pagination and filtering, or fetch one job by ID. Job responses include
the current status, timestamps, priority, type, and stage/output summaries.

## Model Versions

The model registry endpoints allow operators to register and activate model versions. This keeps
workflow records tied to the exact model version used for inference.

## Error Contract

Errors return a stable JSON shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "request_id": "req_..."
  }
}
```

Clients should log `request_id` and send it with support reports.
