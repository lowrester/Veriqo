"""Central import point for all models to ensure proper SQLAlchemy registration."""

from __future__ import annotations

# Import in dependency order to avoid circular imports
# Base models first (no dependencies)
from veriqo.devices.models import Device  # noqa: F401
from veriqo.stations.models import Station  # noqa: F401
from veriqo.users.models import User  # noqa: F401

# Then models that depend on base models
from veriqo.jobs.models import Job, JobHistory, JobStatus  # noqa: F401
from veriqo.evidence.models import Evidence  # noqa: F401
from veriqo.reports.models import Report  # noqa: F401

__all__ = [
    "Device",
    "Station",
    "User",
    "Job",
    "JobHistory",
    "JobStatus",
    "Evidence",
    "Report",
]
