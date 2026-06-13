#!/usr/bin/env python3

"""Registry for pluggable search sources."""

from typing import Dict, List, Type

from tools.logger import get_logger

from .base import SearchSource

logger = get_logger("search")


class SearchSourceRegistry:
    """Global search source registry."""

    _registry: Dict[str, Type[SearchSource]] = {}

    @classmethod
    def register(cls, name: str, source_class: Type[SearchSource]) -> None:
        if not name:
            raise ValueError("Search source name cannot be empty")
        if not issubclass(source_class, SearchSource):
            raise ValueError("Search source class must inherit from SearchSource")
        cls._registry[name.lower()] = source_class
        logger.debug(f"Registered search source: {name} -> {source_class.__name__}")

    @classmethod
    def create(cls, name: str) -> SearchSource:
        key = name.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown search source: {name}. Available: {list(cls._registry.keys())}")
        return cls._registry[key]()

    @classmethod
    def available(cls) -> List[str]:
        return list(cls._registry.keys())


def register_source(name: str, source_class: Type[SearchSource]) -> None:
    """Register a search source class."""
    SearchSourceRegistry.register(name, source_class)


def create_source(name: str) -> SearchSource:
    """Create a search source by name."""
    return SearchSourceRegistry.create(name)


def get_available_sources() -> List[str]:
    """Return available source names."""
    return SearchSourceRegistry.available()
