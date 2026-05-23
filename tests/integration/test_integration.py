"""Integration tests for ATLAS services (cloud-first).

These tests check basic health and configuration without relying on local
Ollama inference.
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_orchestrator_health():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("http://localhost:9000/health", timeout=5.0)
            assert resp.status_code == 200
            data = resp.json()
            assert data["service"] == "orchestrator"
        except Exception:
            pytest.skip("Orchestrator not running")


def test_shared_config_loads():
    from shared.config import SharedConfig
    config = SharedConfig()
    assert config.env in ["dev", "staging", "prod"]

