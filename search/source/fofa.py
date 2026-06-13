#!/usr/bin/env python3

"""FOFA search source."""

import base64
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


class FofaSearchSource(SearchSource):
    """FOFA API search source."""

    name = SearchSourceType.FOFA.value

    def search(self, task: SearchTask, resources) -> SearchResult:
        source_config = resources.config.sources.get(self.name)
        if not source_config:
            return SearchResult()

        api_key = source_config.get_key(task.page)
        if not api_key:
            logger.warning("FOFA source has no API key")
            return SearchResult()

        base_url = trim(source_config.base_url) or "https://fofa.info"
        path = "/api/v1/search/next" if source_config.use_next else "/api/v1/search/all"
        url = f"{base_url.rstrip('/')}{path}"
        page_size = max(1, task.page_size or source_config.page_size)
        encoded_query = base64.b64encode(task.query.encode("utf-8")).decode("utf-8")

        params: Dict[str, Any] = {
            "key": api_key,
            "qbase64": encoded_query,
            "fields": source_config.fields,
            "size": page_size,
        }
        params.update(source_config.extra_params or {})

        if source_config.use_next:
            params["full"] = str(source_config.full).lower()
            if task.cursor:
                params["next"] = task.cursor
        else:
            params["page"] = max(1, task.page)

        try:
            raw = client.http_get(url=url, headers={"Accept": "application/json"}, params=params, timeout=30)
            if not raw:
                return SearchResult()
            data = json.loads(raw)
        except Exception as e:
            logger.error(f"FOFA search failed for query={task.query}: {e}")
            return SearchResult()

        if data.get("error"):
            logger.error(f"FOFA API error for query={task.query}: {data.get('errmsg') or data.get('message')}")
            return SearchResult()

        fields = [field.strip() for field in source_config.fields.split(",") if field.strip()]
        rows = data.get("results") or []
        normalized = [self._normalize_row(row, fields) for row in rows]
        links = self._build_links(normalized)
        content = "\n".join(json.dumps(row, ensure_ascii=False) for row in normalized)

        total = self._int_value(data.get("total") or data.get("size") or len(rows), len(rows))
        if len(rows) >= page_size:
            total = max(total, task.page * page_size + 1)

        next_cursor = trim(str(data.get("next", ""))) if data.get("next") else ""
        return SearchResult(links=links, content=content, total=total, next_cursor=next_cursor)

    def _normalize_row(self, row: Any, fields: List[str]) -> Dict[str, Any]:
        if isinstance(row, dict):
            return row
        if not isinstance(row, list):
            return {"value": row}

        result = {}
        for index, value in enumerate(row):
            field = fields[index] if index < len(fields) else f"field_{index}"
            result[field] = value
        return result

    def _build_links(self, rows: List[Dict[str, Any]]) -> List[str]:
        links = []
        seen = set()
        for row in rows:
            url = self._row_url(row)
            if url and url not in seen:
                seen.add(url)
                links.append(url)
        return links

    def _row_url(self, row: Dict[str, Any]) -> str:
        direct = trim(str(row.get("link") or row.get("url") or ""))
        if direct.startswith("http://") or direct.startswith("https://"):
            return direct

        host = trim(str(row.get("host") or row.get("domain") or row.get("ip") or ""))
        if not host:
            return ""
        if host.startswith("http://") or host.startswith("https://"):
            return host

        protocol = trim(str(row.get("protocol") or "")).lower()
        port = trim(str(row.get("port") or ""))
        scheme = protocol if protocol in ("http", "https") else ("https" if port in ("443", "8443") else "http")

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


register_source(SearchSourceType.FOFA.value, FofaSearchSource)
