# Security

FlowForge is designed as a public-safe project. It includes no private customer records, no live API
keys, and no cloud account credentials.

## Application Controls

- JWT authentication protects write and operator endpoints.
- Role-based authorization separates viewer, operator, and admin capabilities.
- Request-size middleware rejects unexpectedly large payloads.
- Rate limiting protects public endpoints from simple abuse.
- Structured error responses avoid leaking stack traces to clients.
- Passwords are hashed before storage.

## Deployment Controls

- Container runs as a non-root user.
- Kubernetes workloads drop Linux capabilities and disable privilege escalation.
- API and worker deployments set resource requests and limits.
- Network policies restrict in-cluster traffic to API, worker, scheduler, Redis, and PostgreSQL paths.
- Placeholder secrets are documented but not loaded into the production kustomization.

## Secret Handling

Never commit:

- Real database URLs
- JWT signing secrets
- Cloud credentials
- Customer data
- Model vendor API keys

Use local environment variables, Docker Compose overrides, Kubernetes Secrets, or a cloud secret
manager for real deployments.
