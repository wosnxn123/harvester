#!/usr/bin/env python3

"""
Advanced search engine with adaptive query refinement for GitHub code search.
"""

# Explicit re-exports for stable public API
from .client import (
    chat,
    collect,
    estimate_web_total,
    extract,
    get_github_client,
    get_github_stats,
    get_total_num,
    http_get,
    init_github_client,
    log_github_stats,
    search_api_with_count,
    search_code,
    search_github_api,
    search_github_web,
    search_web_with_count,
)
from .source import SearchResult, SearchSource, create_source, get_available_sources, register_source

__all__ = [
    "SearchResult",
    "SearchSource",
    "chat",
    "collect",
    "create_source",
    "estimate_web_total",
    "extract",
    "get_available_sources",
    "get_github_client",
    "get_github_stats",
    "get_total_num",
    "http_get",
    "init_github_client",
    "log_github_stats",
    "register_source",
    "search_api_with_count",
    "search_code",
    "search_github_api",
    "search_github_web",
    "search_web_with_count",
]
