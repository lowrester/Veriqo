import logging
import asyncio

logger = logging.getLogger(__name__)

class EmailMockService:
    """Mock service to simulate sending emails."""

    async def send_completion_email(self, recipient_email: str, recipient_name: str, job_id: str, serial_number: str) -> bool:
        """
        Simulate sending a completion email to the customer.
        """
        logger.info(f"[EMAIL MOCK] Sending completion email to {recipient_name} <{recipient_email}> for Job #{job_id} ({serial_number})")
        
        # Simulate network latency
        await asyncio.sleep(0.3)
        
        # Simulate email content logging
        email_content = f"""
        Subject: Your Device {serial_number} is Ready!
        
        Dear {recipient_name},
        
        Good news! Your device (Serial: {serial_number}) has passed Quality Control and is ready for shipping.
        
        You can view the full test report and status in your customer portal:
        https://veriqo.com/portal/jobs/{job_id}
        
        Thank you for choosing Veriqo.
        """
        logger.info(f"[EMAIL MOCK] Content:\n{email_content}")
        
        return True

email_service = EmailMockService()
