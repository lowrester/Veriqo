import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from veriqko.integrations.picea.client import PiceaClient
from veriqko.integrations.picea.service import PiceaService
from veriqko.jobs.models import Job, TestStep, TestResultStatus

@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.picea_api_url = "https://api.picea.com"
    settings.picea_api_key = "test-key"
    settings.picea_customer_id = "cust-1"
    return settings

@pytest.mark.asyncio
async def test_picea_client_get_results_success(mock_settings):
    client = PiceaClient(mock_settings)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tests": [{"name": "Display", "status": "pass"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        results = await client.get_test_results("SN123")
        
        assert results == {"tests": [{"name": "Display", "status": "pass"}]}
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_picea_service_sync_mapping(mock_settings):
    session = AsyncMock()
    service = PiceaService(session)
    
    # Mock data
    job = Job(id="j1", serial_number="SN1", device_id="d1")
    step = TestStep(id="s1", name="Display", device_id="d1")
    
    picea_data = {
        "tests": [
            {"name": "Display", "status": "pass", "notes": "Crystal clear"}
        ]
    }

    # Setup session mocks
    mock_job_res = MagicMock()
    mock_job_res.scalar_one_or_none.return_value = job
    
    mock_step_res = MagicMock()
    mock_step_res.scalar_one_or_none.return_value = step
    
    mock_existing_res = MagicMock()
    mock_existing_res.scalar_one_or_none.return_value = None

    session.execute.side_effect = [mock_job_res, mock_step_res, mock_existing_res]

    with patch.object(service.client, "get_test_results", new_callable=AsyncMock) as mock_picea:
        mock_picea.return_value = picea_data
        
        success = await service.sync_job_diagnostics("j1", "u1")
        
        assert success is True
        # Verify result was added to session
        added_objects = [item for item in session.add.call_args_list]
        assert len(added_objects) > 0
        result = added_objects[0][0][0]
        assert result.status == TestResultStatus.PASS
        assert "Crystal clear" in result.notes
