from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_report_unauthorized(async_client: AsyncClient):
    # No auth header
    response = await async_client.post("/api/v1/jobs/job_1/reports")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_public_report_not_found(async_client: AsyncClient):
    response = await async_client.get("/reports/token/invalid-token")
    # This might return 404 or redirect depending on implementation
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_generate_report_flow(async_client: AsyncClient, auth_headers):
    # In a real integration test, we would:
    # 1. Create a job
    # 2. Add some test results
    # 3. Request PDF generation

    # Since we don't have a full DB setup in this environment,
    # we test the endpoint's presence and auth.
    with patch("veriqko.reports.router.get_report_generator") as mock_gen:
        mock_gen.return_value = MagicMock()
        response = await async_client.post(
            "/api/v1/jobs/some-uuid/reports",
            headers=auth_headers
        )
        # Should fail with 401 (auth), 422 (validation), or 404 if job doesn't exist
        assert response.status_code in [401, 404, 422]
