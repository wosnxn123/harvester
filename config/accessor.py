#!/usr/bin/env python3

"""
Configuration Accessor

This module provides accessor methods for accessing configuration objects.
It offers type-safe configuration access.

Key Features:
- Type-safe configuration access
- Accessor methods for common configurations
"""

from typing import Optional

from .schemas import (
    Config,
    DisplayConfig,
    GlobalConfig,
    MonitoringConfig,
    PipelineConfig,
    RateLimitConfig,
    SearchSourceConfig,
    TaskConfig,
    WorkerManagerConfig,
)


class ConfigAccessor:
    """Accessor for retrieving configuration objects"""

    def __init__(self, config: Config):
        """Initialize configuration accessor

        Args:
            config: Main configuration object
        """
        self.config = config

    def get_global_config(self) -> GlobalConfig:
        """Get global configuration

        Returns:
            GlobalConfig: Global configuration object
        """
        return self.config.global_config

    def get_pipeline_config(self) -> PipelineConfig:
        """Get pipeline configuration

        Returns:
            PipelineConfig: Pipeline configuration object
        """
        return self.config.pipeline

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get system monitoring configuration

        Returns:
            MonitoringConfig: Monitoring configuration object
        """
        return self.config.monitoring

    def get_display_config(self) -> DisplayConfig:
        """Get display configuration

        Returns:
            DisplayConfig: Display configuration object
        """
        return self.config.display

    def get_task_config(self, task_name: str) -> Optional[TaskConfig]:
        """Get task configuration by name

        Args:
            task_name: Name of the task

        Returns:
            Optional[TaskConfig]: Task configuration or None if not found
        """
        for task in self.config.tasks:
            if task.name == task_name:
                return task
        return None

    def get_enabled_tasks(self) -> list[TaskConfig]:
        """Get all enabled task configurations

        Returns:
            list[TaskConfig]: List of enabled task configurations
        """
        return [task for task in self.config.tasks if task.enabled]

    def get_rate_limit_config(self, name: str) -> Optional[RateLimitConfig]:
        """Get rate limit configuration by name

        Args:
            name: Name of the rate limit configuration

        Returns:
            Optional[RateLimitConfig]: Rate limit configuration or None if not found
        """
        return self.config.ratelimits.get(name)

    def get_search_source_config(self, name: str) -> Optional[SearchSourceConfig]:
        """Get search source configuration by name."""
        return self.config.sources.get(name)

    def get_github_sessions(self) -> list[str]:
        """Get GitHub session tokens

        Returns:
            list[str]: List of GitHub session tokens
        """
        return self.config.global_config.github_credentials.sessions

    def get_github_tokens(self) -> list[str]:
        """Get GitHub API tokens

        Returns:
            list[str]: List of GitHub API tokens
        """
        return self.config.global_config.github_credentials.tokens

    def get_user_agents(self) -> list[str]:
        """Get user agent strings

        Returns:
            list[str]: List of user agent strings
        """
        return self.config.global_config.user_agents

    def get_load_balance_strategy(self) -> str:
        """Get load balance strategy for GitHub credentials

        Returns:
            str: Load balance strategy
        """
        return self.config.global_config.github_credentials.strategy.value

    def get_workspace_dir(self) -> str:
        """Get workspace directory path

        Returns:
            str: Workspace directory path
        """
        return self.config.global_config.workspace

    def get_thread_count(self, stage: str) -> int:
        """Get thread count for a pipeline stage

        Args:
            stage: Pipeline stage name

        Returns:
            int: Thread count for the stage
        """
        return self.config.pipeline.threads.get(stage, 1)

    def get_queue_size(self, stage: str) -> int:
        """Get queue size for a pipeline stage

        Args:
            stage: Pipeline stage name

        Returns:
            int: Queue size for the stage
        """
        return self.config.pipeline.queue_sizes.get(stage, 1000)

    def get_monitoring_thresholds(self) -> dict:
        """Get monitoring thresholds as dictionary

        Returns:
            dict: Monitoring thresholds
        """
        thresholds = self.config.monitoring.thresholds
        return {
            "error_rate": thresholds.error_rate,
            "queue_size": thresholds.queue_size,
            "memory_usage": thresholds.memory_usage,
            "response_time": thresholds.response_time,
        }

    def is_stats_enabled(self) -> bool:
        """Check if statistics display is enabled

        Returns:
            bool: True if statistics display is enabled
        """
        return self.config.monitoring.show_stats

    def get_stats_interval(self) -> int:
        """Get statistics display interval

        Returns:
            int: Statistics display interval in seconds
        """
        return self.config.monitoring.stats_interval

    def get_worker_manager_config(self) -> WorkerManagerConfig:
        """Get worker manager configuration

        Returns:
            WorkerManagerConfig: Worker manager configuration object
        """
        return self.config.worker
