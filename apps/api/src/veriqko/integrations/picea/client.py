import httpx
from typing import Optional, Any, Dict
from veriqko.config import Settings

class PiceaClient:
    """Client for interacting with Picea Diagnostics API."""

    def __init__(self, settings: Settings):
        self.url = settings.picea_api_url
        self.api_key = settings.picea_api_key
        self.customer_id = settings.picea_customer_id
        
        client_kwargs = {
            "timeout": 30.0,
            "headers": {"X-API-KEY": self.api_key} if self.api_key else {}
        }
        if self.url:
            client_kwargs["base_url"] = self.url
            
        self.client = httpx.AsyncClient(**client_kwargs)

    async def get_test_results(self, serial_number: str, imei: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch test results for a specific device.
        Usually queries by Serial Number or IMEI.
        """
        if not self.url or not self.api_key:
            return None

        # Placeholder for actual Picea endpoint structure
        # In many cases, it's something like /v1/reports?identifier=SERIAL
        identifier = imei or serial_number
        try:
            response = await self.client.get(
                "/reports",
                params={"identifier": identifier, "customerId": self.customer_id}
            )
            response.raise_for_status()
            data = response.json()
            
            # Assuming returns a list or direct object
            return data
        except httpx.HTTPStatusError as e:
            import structlog
            structlog.get_logger(__name__).error(
                "Picea API Error",
                status_code=e.response.status_code,
                text=e.response.text,
                identifier=identifier
            )
            return None
        except Exception as e:
            import structlog
            structlog.get_logger(__name__).error(
                "Unexpected error calling Picea",
                error=str(e),
                identifier=identifier
            )
            return None

    async def close(self):
        await self.client.aclose()
