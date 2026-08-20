# Security Policy

## Supported Versions

The `main` branch is the active development line for this demonstration project.

## Reporting a Vulnerability

Do not open a public issue for sensitive reports. Contact the repository owner directly with:

- A summary of the issue
- A reproduction path
- The affected endpoint, command, or deployment asset
- Any logs with secrets removed

## Secret Handling

Never commit real credentials. Use environment variables, Docker Compose overrides, Kubernetes
Secrets, or a cloud secret manager for live deployments.
