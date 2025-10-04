"""
Event model representing a deployment event.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Event(BaseModel):
    """
    Deployment event model.
    """

    id: str
    name: str
    description: str
    origin: str
    destination: str
    date: datetime
    patterns: list[tuple[str, Optional[str]]]
