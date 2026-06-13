#!/usr/bin/env python3

"""GitHub search source adapters."""

from core.enums import SearchSourceType
from core.models import SearchTask
from refine.engine import RefineEngine
from search import client
from tools.logger import get_logger

from .base import SearchResult, SearchSource
from .registry import register_source

logger = get_logger("search")


class GitHubSearchSource(SearchSource):
    """Adapter around the existing GitHub search implementation."""

    name = "github"

    def search(self, task: SearchTask, resources) -> SearchResult:
        use_api = task.source == SearchSourceType.GITHUB_API.value or task.use_api
        page_size = max(1, task.page_size or (100 if use_api else 20))

        if use_api:
            credential = resources.auth.get_token()
        else:
            credential = resources.auth.get_session()

        if not credential:
            logger.warning(f"No GitHub credential available for source: {task.source}")
            return SearchResult()

        query = self._preprocess_query(task.query, use_api)
        results, total, content = client.search_with_count(
            query=query,
            session=credential,
            page=task.page,
            with_api=use_api,
            peer_page=page_size,
        )
        return SearchResult(links=results, content=content, total=total)

    def _preprocess_query(self, query: str, use_api: bool) -> str:
        """GitHub REST search does not support regex syntax."""
        if use_api:
            keyword = RefineEngine.get_instance().clean_regex(query=query)
            if keyword:
                return keyword
        return query


register_source(SearchSourceType.GITHUB_WEB.value, GitHubSearchSource)
register_source(SearchSourceType.GITHUB_API.value, GitHubSearchSource)
