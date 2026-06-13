#!/usr/bin/env python3

"""
Unified Configuration Management System

This package provides a centralized configuration management system that:
- Loads all configuration from a single YAML file
- Provides type-safe configuration access
- Supports default configurations for all modules
- Eliminates duplicate configuration definitions

Usage:
    from config import load_config, get_config

    # Load configuration
    config = load_config("config.yaml")

    # Get specific configuration sections
    global_config = config.global_config
    monitoring_config = config.monitoring
    display_config = config.display
"""

from .accessor import ConfigAccessor
from .loader import ConfigLoader
from .schemas import (
    Config,
    DisplayConfig,
    GlobalConfig,
    MonitoringConfig,
    PipelineConfig,
    SearchSourceConfig,
    StageConfig,
    TaskConfig,
    WorkerManagerConfig,
)

# Global configuration instance
_config_instance = None


def load_config(config_file: str = "config.yaml") -> Config:
    """Load configuration from YAML file

    Args:
        config_file: Path to configuration file

    Returns:
        Config: Loaded configuration object
    """
    global _config_instance
    loader = ConfigLoader(config_file)
    _config_instance = loader.load()
    return _config_instance


def get_config() -> Config:
    """Get current configuration instance

    Returns:
        Config: Current configuration object

    Raises:
        RuntimeError: If configuration not loaded
    """
    if _config_instance is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config_instance


def reload_config(config_file: str = "config.yaml") -> Config:
    """Reload configuration from file

    Args:
        config_file: Path to configuration file

    Returns:
        Config: Reloaded configuration object
    """
    return load_config(config_file)


__all__ = [
    "Config",
    "DisplayConfig",
    "GlobalConfig",
    "MonitoringConfig",
    "PipelineConfig",
    "SearchSourceConfig",
    "StageConfig",
    "SystemMonitoringConfig",
    "TaskConfig",
    "WorkerManagerConfig",
    "ConfigAccessor",
    "ConfigLoader",
    "load_config",
    "get_config",
    "reload_config",
]
