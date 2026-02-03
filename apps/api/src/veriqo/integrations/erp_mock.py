import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ERPMockService:
    """Mock service to simulate connection to an external ERP system (e.g. SAP, NetSuite)."""

    async def sync_part_usage(self, sku: str, quantity: int, job_id: str) -> bool:
        """
        Simulate sending usage data to external ERP.
        In a real app, this would be an HTTP POST request.
        """
        logger.info(f"[ERP SYNC] Sending usage: SKU={sku}, Qty={quantity}, Job={job_id}")
        
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        # Simulate Success
        logger.info(f"[ERP SYNC] Success: Usage recorded in ERP.")
        return True

erp_service = ERPMockService()
