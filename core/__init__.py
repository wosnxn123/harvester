#!/usr/bin/env python3

"""
Core Package - Business Logic and Domain Models

This package contains the core business logic and domain models for the retrieval system.
It focuses on the essential functionality without infrastructure concerns.

Architecture:
- models.py: Core data models, business entities, and task definitions
- types.py: Domain-specific types and interfaces
- exceptions.py: Business-specific exceptions
- enums.py: Domain enumerations

Design Principles:
- Single Responsibility: Each module has a clear business purpose
- Dependency Inversion: Depends on abstractions, not implementations
- Domain-Driven Design: Reflects business concepts and rules
"""

# Authentication services
from .auth import GithubAuthProvider, configure_auth, get_auth_provider

# Domain enumerations
from .enums import ErrorReason, ResultType, SearchSourceType, SystemState

# Business exceptions
from .exceptions import (  # Base exceptions; Specific exceptions
    BaseError,
    BusinessLogicError,
    ConfigurationError,
    CoreException,
    NetworkError,
    ProcessingError,
    RetrievalError,
    ValidationError,
)
from .models import (  # Core models; Task types; Result types
    AcquisitionTask,
    AcquisitionTaskResult,
    CheckTask,
    CheckTaskResult,
    HealthStatus,
    InspectTask,
    InspectTaskResult,
    LogFileInfo,
    LoggingStats,
    ProviderTask,
    ResourceUsage,
    SearchTask,
    SearchTaskResult,
)

# Core types and interfaces
from .types import (  # Abstract interfaces; Type definitions; Data structures
    IAuthProvider,
    IPipelineStats,
    IProvider,
)

# Export all public interfaces
__all__ = [
    # Auth
    "GithubAuthProvider",
    "configure_auth",
    "get_auth_provider",
    # Enums
    "ErrorReason",
    "ResultType",
    "SearchSourceType",
    "SystemState",
    # Exceptions
    "BaseError",
    "NetworkError",
    "ValidationError",
    "CoreException",
    "BusinessLogicError",
    "ProcessingError",
    "RetrievalError",
    "ConfigurationError",
    # Models
    "LogFileInfo",
    "LoggingStats",
    "ResourceUsage",
    "HealthStatus",
    # Types
    "IPipelineStats",
    "IProvider",
    "IAuthProvider",
    # Task types and results
    "ProviderTask",
    "SearchTask",
    "AcquisitionTask",
    "CheckTask",
    "InspectTask",
    "SearchTaskResult",
    "AcquisitionTaskResult",
    "CheckTaskResult",
    "InspectTaskResult",
]
