import os
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from config.loader import ConfigLoader
from core.enums import SearchSourceType
from core.models import SearchTask
from tools.credential import Credentials


class ConfigSourceTests(unittest.TestCase):
    def _load_yaml(self, content: str, env: dict | None = None):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
            handle.write(textwrap.dedent(content))
            path = handle.name
        try:
            with patch.dict(os.environ, env or {}, clear=False):
                return ConfigLoader(path).load()
        finally:
            os.unlink(path)

    def test_fofa_only_config_uses_env_key_without_github_credentials(self):
        config = self._load_yaml(
            """
            global:
              workspace: "./data"
            sources:
              fofa:
                enabled: true
                page_size: 2
                max_pages: 2
                max_results: 4
            tasks:
              - name: openai
                enabled: true
                provider_type: openai_like
                sources: ["fofa"]
                api:
                  base_url: https://api.openai.com
                  completion_path: /v1/chat/completions
                  model_path: /v1/models
                  default_model: gpt-4o-mini
                patterns:
                  key_pattern: "sk-[A-Z0-9]+"
                conditions:
                  - source_queries:
                      fofa: 'body="sk-"'
            """,
            env={"FOFA_KEY": "fofa-test-key"},
        )

        self.assertEqual(config.sources["fofa"].api_keys, ["fofa-test-key"])
        self.assertEqual(config.tasks[0].conditions[0].source_queries["fofa"], 'body="sk-"')

    def test_legacy_task_sources_fall_back_to_github_api(self):
        config = self._load_yaml(
            """
            global:
              workspace: "./data"
            tasks:
              - name: openai
                enabled: true
                provider_type: openai_like
                use_api: true
                api:
                  base_url: https://api.openai.com
                  completion_path: /v1/chat/completions
                  model_path: /v1/models
                  default_model: gpt-4o-mini
                patterns:
                  key_pattern: "sk-[A-Z0-9]+"
                conditions:
                  - query: '"sk-"'
            """,
            env={"GITHUB_TOKENS": "ghp-test"},
        )

        self.assertEqual(config.tasks[0].sources, [])
        self.assertIn(SearchSourceType.GITHUB_API.value, config.sources)

    def test_old_search_task_deserialization_defaults_source(self):
        task = SearchTask.from_dict(
            {
                "type": "SearchTask",
                "task_id": "old-task",
                "provider": "openai",
                "created_at": 1.0,
                "attempts": 0,
                "data": {"query": '"sk-"', "regex": "sk-[A-Z0-9]+", "page": 1, "use_api": False},
            }
        )

        self.assertEqual(task.source, SearchSourceType.GITHUB_WEB.value)

    def test_empty_github_credentials_are_allowed_until_requested(self):
        credentials = Credentials(sessions=[], tokens=[])

        self.assertIsNone(credentials.get_session())
        self.assertIsNone(credentials.get_token())
        with self.assertRaises(RuntimeError):
            credentials.get_credential()


if __name__ == "__main__":
    unittest.main()
