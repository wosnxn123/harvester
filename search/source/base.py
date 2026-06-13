#!/usr/bin/env python3

"""Search source abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from core.models import SearchTask


@dataclass
class SearchResult:
    """Normalized output from a search source."""

    links: List[str] = field(default_factory=list)
    content: str = ""
    total: int = 0
    next_cursor: str = ""


class SearchSource(ABC):
    """Base class for pluggable search sources."""

    name: str = ""

    @abstractmethod
    def search(self, task: SearchTask, resources) -> SearchResult:
        """Execute a search task and return normalized results."""
        pass
