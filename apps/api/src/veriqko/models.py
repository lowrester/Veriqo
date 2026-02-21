"""Central import point for all models to ensure proper SQLAlchemy registration."""

from __future__ import annotations

# Import in dependency order to avoid circular imports
# Base models first (no dependencies)
from veriqko.devices.models import Brand, Device, GadgetType  # noqa: F401
from veriqko.evidence.models import Evidence  # noqa: F401

# Then models that depend on base models
from veriqko.jobs.models import Job, JobHistory, JobStatus  # noqa: F401
from veriqko.parts.models import Part, PartUsage  # noqa: F401
from veriqko.printing.models import LabelTemplate  # noqa: F401
from veriqko.reports.models import Report  # noqa: F401
from veriqko.stations.models import Station  # noqa: F401
from veriqko.users.models import User  # noqa: F401

__all__ = [
    "Device",
    "Brand",
    "GadgetType",
    "Station",
    "User",
    "Job",
    "JobHistory",
    "JobStatus",
    "Evidence",
    "Report",
    "Part",
    "PartUsage",
    "LabelTemplate",
]
