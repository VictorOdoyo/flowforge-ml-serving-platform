import asyncio
import os

import httpx


async def smoke_test() -> None:
    base_url = os.getenv("FLOWFORGE_BASE_URL", "http://localhost:8000")
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        health = await client.get("/api/v1/health")
        health.raise_for_status()
        readiness = await client.get("/api/v1/ready")
        readiness.raise_for_status()
        schema = await client.get("/openapi.json")
        schema.raise_for_status()

    paths = schema.json()["paths"]
    required_paths = {"/api/v1/jobs", "/api/v1/models", "/api/v1/auth/token"}
    missing = required_paths.difference(paths)
    if missing:
        raise RuntimeError(f"OpenAPI schema is missing required paths: {sorted(missing)}")
    print(f"FlowForge smoke test passed against {base_url}")


if __name__ == "__main__":
    asyncio.run(smoke_test())
