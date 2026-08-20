# Deployment

FlowForge ships with Docker Compose for local integration and Kubernetes manifests for production
style review.

## Docker Compose

```bash
docker compose up --build
```

Compose starts:

- PostgreSQL
- Redis
- Alembic migration runner
- FastAPI application
- Celery worker
- Celery beat scheduler
- Nginx gateway

The gateway listens on `http://localhost:8080`.

## Kubernetes

The Kubernetes manifests live in `deploy/k8s`.

```bash
kubectl kustomize deploy/k8s
```

Before applying the manifests, create a real secret named `flowforge-secrets` using the shape shown
in `deploy/k8s/secret.example.yaml`.

```bash
kubectl apply -k deploy/k8s
```

## Production Notes

- Replace `flowforge.local` in the Ingress with a real domain.
- Use an external managed PostgreSQL database for production traffic.
- Use a managed Redis service or a highly available in-cluster Redis deployment.
- Rotate JWT secrets and database credentials outside of source control.
- Pin image tags for production releases instead of deploying `latest`.
