"""Common data structures used across multiple models."""

from typing import Optional, Dict, Any
from pydantic import Field
from .base import TroveBaseModel


class Identifier(TroveBaseModel):
    """Represents an identifier object."""
    type: Optional[str] = None
    linktype: Optional[str] = None
    value: Optional[str] = None


class Language(TroveBaseModel):
    """Represents a language object."""
    code: Optional[str] = None
    name: Optional[str] = None


class Spatial(TroveBaseModel):
    """Represents spatial/geographic information."""
    type: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None


class ItemCount(TroveBaseModel):
    """Represents count information for user-generated content."""
    value: Optional[int] = None
    by: Optional[str] = None


class Tag(TroveBaseModel):
    """Represents a user tag."""
    id: Optional[str] = None
    text: Optional[str] = None
    by: Optional[str] = None
    lastupdated: Optional[str] = None


class Comment(TroveBaseModel):
    """Represents a user comment."""
    id: Optional[str] = None
    text: Optional[str] = None
    by: Optional[str] = None
    lastupdated: Optional[str] = None


class Relevance(TroveBaseModel):
    """Represents relevance scoring information."""
    score: Optional[float] = None
    value: Optional[str] = None