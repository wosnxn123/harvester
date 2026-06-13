#!/usr/bin/env python3

"""Shodan search source."""

import json
from typing import Any, Dict, List

from core.enums import SearchSourceType
from core.models import SearchTask
from search import client
from tools.logger import get_logger
from tools.utils import trim

from .base import SearchResult, SearchSource
from .registry import register_source

logger = get_logger("search")


class ShodanSearchSource(SearchSource):
    """Shodan REST search source."""

    name = SearchSourceType.SHODAN.value

    def search(self, task: SearchTask, resources) -> SearchResult:
        source_config = resources.config.sources.get(self.name)
        if not source_config:
            return SearchResult()

        api_key = source_config.get_key(task.page)
        if not api_key:
            logger.warning("Shodan source has no API key")
            return SearchResult()

        base_url = trim(source_config.base_url) or "https://api.shodan.io"
        url = f"{base_url.rstrip('/')}/shodan/host/search"
        params: Dict[str, Any] = {
            "key": api_key,
            "query": task.query,
            "page": max(1, task.page),
            "minify": str(source_config.minify).lower(),
        }
        if source_config.fields:
            params["fields"] = source_config.fields
        params.update(source_config.extra_params or {})

        try:
            raw = client.http_get(url=url, headers={"Accept": "application/json"}, params=params, timeout=30)
            if not raw:
                return SearchResult()
            data = json.loads(raw)
        except Exception as e:
            logger.error(f"Shodan search failed for query={task.query}: {e}")
            return SearchResult()

        if data.get("error"):
            logger.error(f"Shodan API error for query={task.query}: {data.get('error')}")
            return SearchResult()

        matches = data.get("matches") or []
        links = self._build_links(matches)
        content = "\n".join(json.dumps(match, ensure_ascii=False) for match in matches)
        total = self._int_value(data.get("total"), len(matches))
        return SearchResult(links=links, content=content, total=total)

    def _build_links(self, matches: List[Dict[str, Any]]) -> List[str]:
        links = []
        seen = set()
        for match in matches:
            url = self._match_url(match)
            if url and url not in seen:
                seen.add(url)
                links.append(url)
        return links

    def _match_url(self, match: Dict[str, Any]) -> str:
        host = ""
        hostnames = match.get("hostnames") or []
        domains = match.get("domains") or []
        if isinstance(hostnames, list) and hostnames:
            host = str(hostnames[0])
        elif isinstance(domains, list) and domains:
            host = str(domains[0])
        else:
            host = str(match.get("ip_str") or "")

        host = trim(host)
        if not host:
            return ""

        port = trim(str(match.get("port") or ""))
        transport = trim(str(match.get("transport") or "")).lower()
        has_ssl = bool(match.get("ssl"))
        scheme = "https" if has_ssl or port in ("443", "8443") else "http"
        if transport in ("http", "https"):
            scheme = transport

        netloc = host
        if ":" not in netloc and port and not (scheme == "http" and port == "80") and not (
            scheme == "https" and port == "443"
        ):
            netloc = f"{netloc}:{port}"
        return f"{scheme}://{netloc}"

    def _int_value(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default


register_source(SearchSourceType.SHODAN.value, ShodanSearchSource)
