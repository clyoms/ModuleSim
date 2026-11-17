"""Event bus component (Simplified: an in-app message passer, not a real queue)."""

from .bus import EventBus
from . import messages

__all__ = ["EventBus", "messages"]
