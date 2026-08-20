# Operations

## Health Checks

- `/api/v1/health` confirms the application process is alive.
- `/api/v1/ready` checks PostgreSQL and Redis reachability.
- `/metrics` exposes Prometheus metrics.

## Useful Commands

Run migrations:

```bash
uv run alembic upgrade head
```

Seed a local admin account:

```bash
uv run python scripts/seed_admin.py
```

Run a smoke test:

```bash
uv run python scripts/smoke_test.py
```

Validate Kubernetes manifests:

```bash
kubectl kustomize deploy/k8s
```

## Monitoring Signals

Watch for:

- Readiness failures
- Growing queued job count
- Repeated retrying jobs
- Elevated HTTP 4xx and 5xx rates
- Slow request latency
- Redis broker connectivity errors
- PostgreSQL connection pool pressure

## Incident Response

1. Confirm datastore health.
2. Inspect worker logs for retry patterns.
3. Check recent deployments and migrations.
4. Pause external submissions if duplicate traffic is suspected.
5. Re-run failed jobs only after idempotency records and output state are understood.
