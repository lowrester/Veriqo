import asyncio
import os
import subprocess
from datetime import datetime

from pydantic import BaseModel


class SystemVersion(BaseModel):
    current_version: str
    latest_version: str
    is_update_available: bool
    last_checked: datetime

class UpdateStatus(BaseModel):
    is_updating: bool
    current_step: str
    progress_percent: int
    last_log: str
    error: str | None = None

class SystemService:
    """Service for managing system updates and version checking."""

    UPDATE_SCRIPT_PATH = "scripts/system_update.sh"
    STATUS_FILE = "/opt/veriqko/update_status.json"

    async def get_current_version(self) -> str:
        """Get current git hash or tag."""
        try:
            # First try git describe for tag
            process = await asyncio.create_subprocess_shell(
                "git describe --tags",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode().strip()

            # Fallback to short hash
            process = await asyncio.create_subprocess_shell(
                "git rev-parse --short HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode().strip()
        except Exception:
            return "unknown"

    async def check_for_updates(self) -> SystemVersion:
        """Fetch remote tags and compare with current."""
        # Fetch latest
        await asyncio.create_subprocess_shell("git fetch --tags")

        current = await self.get_current_version()

        # Get latest remote tag
        process = await asyncio.create_subprocess_shell(
            "git describe --tags $(git rev-list --tags --max-count=1)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        latest = stdout.decode().strip() or current

        return SystemVersion(
            current_version=current,
            latest_version=latest,
            is_update_available=current != latest,
            last_checked=datetime.now()
        )

    def trigger_update(self, target_version: str = "main") -> None:
        """
        Trigger the background update script.
        We use subprocess.Popen with nohup to detach it completely.
        """
        # Ensure script is executable
        os.chmod(self.UPDATE_SCRIPT_PATH, 0o755)

        # Run detached
        subprocess.Popen(
            ["nohup", self.UPDATE_SCRIPT_PATH, target_version, "&"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )

    async def get_update_status(self) -> UpdateStatus:
        """Read the status file written by the update script."""
        # Mock status for now until we implement the script writing logic
        # In production this would read a JSON file from /tmp or /opt/veriqko
        if os.path.exists(self.STATUS_FILE):
             # Read file logic here (omitted for MVP start)
             pass

        return UpdateStatus(
            is_updating=False,
            current_step="Idle",
            progress_percent=0,
            last_log=""
        )

# Global instance
system_service = SystemService()
