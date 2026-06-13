import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config.schemas import Config
from core.enums import SearchSourceType
from core.models import SearchTask
from search.source.fofa import FofaSearchSource
from search.source.shodan import ShodanSearchSource
from stage.base import StageOutput
from stage.definition import SearchStage


class SearchSourceMappingTests(unittest.TestCase):
    def _resources(self):
        config = Config()
        config.sources["fofa"].enabled = True
        config.sources["fofa"].api_keys = ["fofa-key"]
        config.sources["fofa"].api_key = "fofa-key"
        config.sources["fofa"].fields = "host,ip,port,protocol,title,banner"
        config.sources["fofa"].page_size = 2
        config.sources["fofa"].max_pages = 2
        config.sources["fofa"].max_results = 3
        config.sources["fofa"].use_next = True

        config.sources["shodan"].enabled = True
        config.sources["shodan"].api_keys = ["shodan-key"]
        config.sources["shodan"].api_key = "shodan-key"
        config.sources["shodan"].page_size = 100
        config.sources["shodan"].max_pages = 3
        config.sources["shodan"].max_results = 250

        return SimpleNamespace(config=config)

    def test_fofa_maps_rows_to_links_content_and_cursor(self):
        payload = {
            "error": False,
            "results": [
                ["example.com", "203.0.113.1", "443", "https", "title", "leaked sk-ABC123"],
                ["http://plain.example", "203.0.113.2", "80", "http", "title", "none"],
            ],
            "next": "cursor-2",
        }

        with patch("search.client.http_get", return_value=json.dumps(payload)):
            result = FofaSearchSource().search(
                SearchTask(
                    provider="openai",
                    source=SearchSourceType.FOFA.value,
                    query='body="sk-"',
                    regex="sk-[A-Z0-9]+",
                    page_size=2,
                    max_pages=2,
                    max_results=3,
                ),
                self._resources(),
            )

        self.assertEqual(result.links[0], "https://example.com")
        self.assertIn("http://plain.example", result.links)
        self.assertIn("sk-ABC123", result.content)
        self.assertEqual(result.next_cursor, "cursor-2")

    def test_shodan_maps_matches_to_links_and_content(self):
        payload = {
            "total": 120,
            "matches": [
                {
                    "ip_str": "203.0.113.10",
                    "port": 443,
                    "hostnames": ["api.example.com"],
                    "ssl": {"cert": {}},
                    "data": "contains sk-XYZ789",
                }
            ],
        }

        with patch("search.client.http_get", return_value=json.dumps(payload)):
            result = ShodanSearchSource().search(
                SearchTask(
                    provider="openai",
                    source=SearchSourceType.SHODAN.value,
                    query='"sk-"',
                    regex="sk-[A-Z0-9]+",
                ),
                self._resources(),
            )

        self.assertEqual(result.links, ["https://api.example.com"])
        self.assertIn("sk-XYZ789", result.content)
        self.assertEqual(result.total, 120)

    def test_stage_limits_page_fanout_by_max_pages_and_max_results(self):
        resources = SimpleNamespace(
            config=self._resources().config,
            limiter=None,
            auth=None,
            providers={},
            task_configs={},
        )
        stage = SearchStage(resources=resources, handler=lambda output: None, thread_count=1, queue_size=10)
        task = SearchTask(
            provider="openai",
            source=SearchSourceType.SHODAN.value,
            query='"sk-"',
            regex="sk-[A-Z0-9]+",
            page=1,
            page_size=100,
            max_pages=3,
            max_results=250,
        )
        output = StageOutput(task=task)

        stage._handle_pagination(task, total=1000, next_cursor="", output=output)

        pages = [new_task.page for new_task, target in output.new_tasks]
        self.assertEqual(pages, [2, 3])


if __name__ == "__main__":
    unittest.main()
