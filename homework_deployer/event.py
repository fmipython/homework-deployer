"""
Event model representing a deployment event.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    Deployment event model.
    """

    id: str = Field(exclude=True, default="")
    name: str
    description: str
    origin: str
    destination: str
    date: datetime
    patterns: list[tuple[str, Optional[str]]]
    is_dry_run: bool = False
