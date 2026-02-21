"""Security utilities for Job processing."""


import structlog

logger = structlog.get_logger(__name__)

async def check_imei_blacklist(imei: str) -> tuple[bool, str | None]:
    """
    Check if an IMEI is blacklisted (e.g. GSMA, Police).
    Returning (is_blacklisted, reason).
    
    This is a plumbing implementation that can be extended with real API calls.
    Specific test IMEIs can be used to simulate blacklist hits.
    """
    if not imei:
        return False, None

    # Standard test IMEI for "Lost/Stolen"
    if imei == "000000000000000":
        return True, "Reported as Lost/Stolen (GSMA)"

    if imei == "111111111111111":
        return True, "Financed / Unpaid (Operator Lock)"

    # Mock success path
    logger.info("IMEI security check passed", imei=imei)
    return False, None
