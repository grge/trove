"""Type stubs for trove package."""

from typing import Optional
from .client import TroveClient
from .config import TroveConfig
from .search import Search

__version__: str

def __getattr__(name: str) -> None: ...

# Main exports
__all__ = ["TroveClient", "TroveConfig", "Search"]