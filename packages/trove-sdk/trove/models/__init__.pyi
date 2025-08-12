"""Type stubs for trove.models package."""

from typing import Dict, Any, Optional, Union, List
from .work import Work, WorkVersion, WorkHolding
from .article import Article, ArticleTitle
from .people import People, Biography
from .list import TroveList, ListItem
from .common import Identifier, Language, Spatial, ItemCount, Tag, Comment, Relevance

MODEL_REGISTRY: Dict[str, type]

def parse_record(
    record_data: Dict[str, Any], 
    record_type: str
) -> Optional[Union[Work, Article, People, TroveList]]: ...

def parse_records(records_data: Dict[str, Any]) -> Dict[str, Any]: ...

__all__ = [
    "Work", "WorkVersion", "WorkHolding",
    "Article", "ArticleTitle", 
    "People", "Biography",
    "TroveList", "ListItem",
    "Identifier", "Language", "Spatial", "ItemCount", "Tag", "Comment", "Relevance",
    "parse_record", "parse_records", "MODEL_REGISTRY"
]