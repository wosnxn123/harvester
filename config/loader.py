#!/usr/bin/env python3

"""
Configuration Loader

This module provides unified YAML configuration loading functionality.
It replaces the scattered configuration loading logic throughout the application.

Key Features:
- Single YAML file loading
- Default configuration generation
- Type-safe configuration parsing
- Validation integration
"""

import os
from typing import Any, Dict

import yaml

from core.models import Condition, Patterns, RateLimitConfig, inherit_patterns

from .defaults import get_default_config
from .schemas import (
    ApiConfig,
    Config,
    CredentialsConfig,
    DisplayConfig,
    DisplayContextConfig,
    GlobalConfig,
    LoadBalanceStrategy,
    MonitoringConfig,
    PersistenceConfig,
    PipelineConfig,
    SearchSourceConfig,
    StageConfig,
    TaskConfig,
    WorkerManagerConfig,
)
from .validator import ConfigValidator


class ConfigLoader:
    """Unified configuration loader for YAML files"""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration loader

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.validator = ConfigValidator()

    def load(self) -> Config:
        """Load configuration from YAML file

        Returns:
            Config: Loaded and validated configuration object
        """
        if not os.path.exists(self.config_file):
            self._create_default_config()

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            config = self._parse_config(data)
            self.validator.validate(config)
            return config

        except Exception as e:
            raise RuntimeError(f"Failed to load config file {self.config_file}: {e}")

    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """Parse YAML data into Config object

        Args:
            data: Raw YAML data

        Returns:
            Config: Parsed configuration object
        """
        config = Config()

        # Parse global configuration
        if "global" in data:
            config.global_config = self._parse_global_config(data["global"])

        # Parse pipeline configuration
        if "pipeline" in data:
            config.pipeline = self._parse_pipeline_config(data["pipeline"])

        # Parse monitoring configuration
        if "monitoring" in data:
            config.monitoring = self._parse_monitoring_config(data["monitoring"])

        # Parse display configuration
        if "display" in data:
            config.display = self._parse_display_config(data["display"])

        # Parse persistence configuration
        if "persistence" in data:
            config.persistence = self._parse_persistence_config(data["persistence"])

        # Parse worker configuration
        if "worker" in data:
            config.worker = self._parse_worker_manager_config(data["worker"])

        # Parse search sources before tasks so task validation can inspect them
        if "sources" in data:
            config.sources = self._parse_sources(data["sources"], config.sources)
        else:
            config.sources = self._parse_sources({}, config.sources)

        # Parse rate limits
        if "ratelimits" in data:
            config.ratelimits = self._parse_rate_limits(data["ratelimits"])

        # Parse tasks
        if "tasks" in data:
            config.tasks = [self._parse_task_config(task_data) for task_data in data["tasks"]]

        return config

    def _parse_global_config(self, data: Dict[str, Any]) -> GlobalConfig:
        """Parse global configuration section

        Args:
            data: Global configuration data

        Returns:
            GlobalConfig: Parsed global configuration
        """
        credentials_data = data.get("github_credentials", {})

        # Get sessions and tokens from config
        sessions = credentials_data.get("sessions") or []
        tokens = credentials_data.get("tokens") or []

        # Filter out placeholder values from config
        valid_sessions = [s for s in sessions if s and not s.startswith("your_")]
        valid_tokens = [t for t in tokens if t and not t.startswith("your_")]

        # If both valid sessions and tokens are empty, try to read from environment variables
        if not valid_sessions and not valid_tokens:
            # Try to read GitHub sessions from GITHUB_SESSIONS environment variable
            github_sessions = os.getenv("GITHUB_SESSIONS")
            if github_sessions:
                valid_sessions = [s.strip() for s in github_sessions.split(",") if s.strip()]

            # Try to read GitHub tokens from GITHUB_TOKENS environment variable
            github_tokens = os.getenv("GITHUB_TOKENS")
            if github_tokens:
                valid_tokens = [t.strip() for t in github_tokens.split(",") if t.strip()]

        credentials = CredentialsConfig(
            sessions=valid_sessions,
            tokens=valid_tokens,
            strategy=LoadBalanceStrategy(credentials_data.get("strategy", "round_robin")),
        )

        return GlobalConfig(
            workspace=os.path.abspath(data.get("workspace", "./data")),
            max_retries_requeued=data.get("max_retries_requeued", 3),
            github_credentials=credentials,
            user_agents=data.get("user_agents", []),
        )

    def _parse_pipeline_config(self, data: Dict[str, Any]) -> PipelineConfig:
        """Parse pipeline configuration section

        Args:
            data: Pipeline configuration data

        Returns:
            PipelineConfig: Parsed pipeline configuration
        """
        return PipelineConfig(threads=data.get("threads", {}), queue_sizes=data.get("queue_sizes", {}))

    def _parse_monitoring_config(self, data: Dict[str, Any]) -> MonitoringConfig:
        """Parse system monitoring configuration section

        Args:
            data: Monitoring configuration data

        Returns:
            MonitoringConfig: Parsed monitoring configuration
        """
        return MonitoringConfig(
            update_interval=data.get("update_interval", 2.0),
            error_threshold=data.get("error_threshold", 0.1),
            queue_threshold=data.get("queue_threshold", 1000),
            memory_threshold=data.get("memory_threshold", 1073741824),
            response_threshold=data.get("response_threshold", 5.0),
        )

    def _parse_display_config(self, data: Dict[str, Any]) -> DisplayConfig:
        """Parse display configuration section

        Args:
            data: Display configuration data

        Returns:
            DisplayConfig: Parsed display configuration
        """
        contexts = {}
        contexts_data = data.get("contexts", {})

        for context_name, modes_data in contexts_data.items():
            contexts[context_name] = {}
            for mode_name, mode_data in modes_data.items():
                contexts[context_name][mode_name] = DisplayContextConfig(
                    title=mode_data.get("title", ""),
                    show_workers=mode_data.get("show_workers", True),
                    show_alerts=mode_data.get("show_alerts", True),
                    show_performance=mode_data.get("show_performance", False),
                    show_newline_prefix=mode_data.get("show_newline_prefix", False),
                    width=mode_data.get("width", 80),
                    max_alerts_per_level=mode_data.get("max_alerts_per_level", 3),
                )

        return DisplayConfig(contexts=contexts)

    def _parse_persistence_config(self, data: Dict[str, Any]) -> PersistenceConfig:
        """Parse persistence configuration section

        Args:
            data: Persistence configuration data

        Returns:
            PersistenceConfig: Parsed persistence configuration
        """
        return PersistenceConfig(
            batch_size=data.get("batch_size", 50),
            save_interval=data.get("save_interval", 30),
            queue_interval=data.get("queue_interval", 60),
            auto_restore=data.get("auto_restore", True),
            shutdown_timeout=data.get("shutdown_timeout", 30),
            simple=data.get("format", "txt").strip().lower() == "txt",
        )

    def _parse_worker_manager_config(self, data: Dict[str, Any]) -> WorkerManagerConfig:
        """Parse worker manager configuration section

        Args:
            data: Worker manager configuration data

        Returns:
            WorkerManagerConfig: Parsed worker manager configuration
        """
        return WorkerManagerConfig(
            enabled=data.get("enabled", False),
            min_workers=data.get("min_workers", 1),
            max_workers=data.get("max_workers", 10),
            target_queue_size=data.get("target_queue_size", 100),
            adjustment_interval=data.get("adjustment_interval", 5.0),
            scale_up_threshold=data.get("scale_up_threshold", 0.8),
            scale_down_threshold=data.get("scale_down_threshold", 0.2),
            log_recommendations=data.get("log_recommendations", True),
        )

    def _parse_rate_limits(self, data: Dict[str, Any]) -> Dict[str, RateLimitConfig]:
        """Parse rate limits configuration section

        Args:
            data: Rate limits configuration data

        Returns:
            Dict[str, RateLimitConfig]: Parsed rate limits
        """
        rate_limits = {}
        for name, limit_data in data.items():
            rate_limits[name] = RateLimitConfig(
                base_rate=limit_data.get("base_rate", 1.0),
                burst_limit=limit_data.get("burst_limit", 5),
                adaptive=limit_data.get("adaptive", True),
                backoff_factor=limit_data.get("backoff_factor", 0.5),
                recovery_factor=limit_data.get("recovery_factor", 1.1),
                max_rate_multiplier=limit_data.get("max_rate_multiplier", 2.0),
                min_rate_multiplier=limit_data.get("min_rate_multiplier", 0.1),
            )
        return rate_limits

    def _parse_sources(
        self, data: Dict[str, Any], defaults: Dict[str, SearchSourceConfig]
    ) -> Dict[str, SearchSourceConfig]:
        """Parse search source configuration with built-in defaults."""
        sources = dict(defaults)
        for name, source_data in (data or {}).items():
            if not isinstance(source_data, dict):
                source_data = {}
            default = sources.get(name, SearchSourceConfig())
            sources[name] = self._parse_source_config(name, source_data, default)

        # Environment variables can enable FOFA/Shodan credentials without YAML edits.
        if "fofa" in sources and not sources["fofa"].api_keys:
            fofa_key = os.getenv("FOFA_KEY", "")
            if fofa_key:
                sources["fofa"].api_keys = [fofa_key.strip()]
                sources["fofa"].api_key = sources["fofa"].api_keys[0]

        if "shodan" in sources and not sources["shodan"].api_keys:
            shodan_keys = os.getenv("SHODAN_API_KEYS") or os.getenv("SHODAN_API_KEY") or ""
            keys = [key.strip() for key in shodan_keys.split(",") if key.strip()]
            if keys:
                sources["shodan"].api_keys = keys
                sources["shodan"].api_key = keys[0]

        return sources

    def _parse_source_config(
        self, name: str, data: Dict[str, Any], default: SearchSourceConfig
    ) -> SearchSourceConfig:
        """Parse one search source config."""
        rate_limit_data = data.get("rate_limit", {})
        if rate_limit_data:
            rate_limit = RateLimitConfig(
                base_rate=rate_limit_data.get("base_rate", default.rate_limit.base_rate),
                burst_limit=rate_limit_data.get("burst_limit", default.rate_limit.burst_limit),
                adaptive=rate_limit_data.get("adaptive", default.rate_limit.adaptive),
                backoff_factor=rate_limit_data.get("backoff_factor", default.rate_limit.backoff_factor),
                recovery_factor=rate_limit_data.get("recovery_factor", default.rate_limit.recovery_factor),
                max_rate_multiplier=rate_limit_data.get(
                    "max_rate_multiplier", default.rate_limit.max_rate_multiplier
                ),
                min_rate_multiplier=rate_limit_data.get(
                    "min_rate_multiplier", default.rate_limit.min_rate_multiplier
                ),
            )
        else:
            rate_limit = default.rate_limit

        api_keys = data.get("api_keys", default.api_keys)
        if isinstance(api_keys, str):
            api_keys = [key.strip() for key in api_keys.split(",") if key.strip()]
        else:
            api_keys = list(api_keys or [])

        api_key = data.get("api_key", data.get("key", default.api_key))
        if api_key and api_key not in api_keys:
            api_keys = [api_key] + list(api_keys)

        return SearchSourceConfig(
            enabled=data.get("enabled", default.enabled),
            base_url=data.get("base_url", default.base_url),
            api_key=api_key,
            api_keys=api_keys,
            fields=data.get("fields", default.fields),
            page_size=data.get("page_size", default.page_size),
            max_pages=data.get("max_pages", default.max_pages),
            max_results=data.get("max_results", default.max_results),
            use_next=data.get("use_next", default.use_next),
            full=data.get("full", default.full),
            minify=data.get("minify", default.minify),
            rate_limit=rate_limit,
            extra_params=data.get("extra_params", default.extra_params),
        )

    def _parse_task_config(self, data: Dict[str, Any]) -> TaskConfig:
        """Parse task configuration

        Args:
            data: Task configuration data

        Returns:
            TaskConfig: Parsed task configuration
        """
        # Parse stages
        stages_data = data.get("stages", {})
        stages = StageConfig(
            search=stages_data.get("search", True),
            gather=stages_data.get("gather", True),
            check=stages_data.get("check", True),
            inspect=stages_data.get("inspect", True),
        )

        # Parse API configuration
        api_data = data.get("api", {})
        api = ApiConfig(
            base_url=api_data.get("base_url", ""),
            completion_path=api_data.get("completion_path", "/v1/chat/completions"),
            model_path=api_data.get("model_path", "/v1/models"),
            default_model=api_data.get("default_model", ""),
            auth_key=api_data.get("auth_key", "Authorization"),
            extra_headers=api_data.get("extra_headers", {}),
            api_version=api_data.get("api_version", ""),
            timeout=api_data.get("timeout", 30),
            retries=api_data.get("retries", 3),
        )

        # Parse patterns
        patterns_data = data.get("patterns", {})
        patterns = Patterns(
            key_pattern=patterns_data.get("key_pattern", ""),
            address_pattern=patterns_data.get("address_pattern", ""),
            endpoint_pattern=patterns_data.get("endpoint_pattern", ""),
            model_pattern=patterns_data.get("model_pattern", ""),
        )

        # Parse conditions
        conditions_data = data.get("conditions", [])
        conditions = []
        for condition_data in conditions_data:
            condition = Condition.from_dict(condition_data)
            # Inherit global patterns if condition patterns are empty
            inherit_patterns(patterns, condition)
            conditions.append(condition)

        # Parse rate limit
        rate_limit_data = data.get("rate_limit", {})
        rate_limit = RateLimitConfig(
            base_rate=rate_limit_data.get("base_rate", 1.0),
            burst_limit=rate_limit_data.get("burst_limit", 5),
            adaptive=rate_limit_data.get("adaptive", True),
        )

        return TaskConfig(
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            provider_type=data.get("provider_type", ""),
            use_api=data.get("use_api", False),
            sources=data.get("sources", []),
            stages=stages,
            extras=data.get("extras", {}),
            api=api,
            patterns=patterns,
            conditions=conditions,
            rate_limit=rate_limit,
        )

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        default_config = get_default_config()

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"Created default configuration file: {self.config_file}")
        print("Please edit the configuration file and set your GitHub credentials and other settings")
