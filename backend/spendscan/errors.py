"""Shared SpendScan error hierarchy."""

from __future__ import annotations


class SpendScanError(Exception):
    """Base error for SpendScan domain failures."""


class ConfigurationError(SpendScanError):
    """Application configuration is missing or invalid."""


class ExternalServiceError(SpendScanError):
    """External service call failed."""


class OutputValidationError(SpendScanError):
    """Model output could not be parsed into the expected schema."""
