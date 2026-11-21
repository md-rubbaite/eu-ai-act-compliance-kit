"""EU AI Act compliance kit: classify AI systems, list obligations with dates, and gate on missing evidence."""

from .assess import Assessment, assess
from .model import ProfileError, SystemProfile, load_profile, parse_profile

__all__ = ["Assessment", "ProfileError", "SystemProfile", "assess", "load_profile", "parse_profile"]
__version__ = "1.0.0"
