# Titan V11.3 — Core modules
"""
Core package exports for cleaner imports.
Usage:
    from core import AnomalyPatcher, ProfileInjector, AndroidProfileForge
    from core.exceptions import TitanError, ADBConnectionError
    from core.models import PatchPhase, JobStatus, DeviceState
"""

from exceptions import (
    TitanError,
    ADBConnectionError,
    ADBCommandError,
    DeviceOfflineError,
    DeviceNotFoundError,
    PatchPhaseError,
    ResetpropError,
    ProfileForgeError,
    InjectionError,
    WalletProvisionError,
    GAppsBootstrapError,
)

__all__ = [
    "TitanError",
    "ADBConnectionError",
    "ADBCommandError",
    "DeviceOfflineError",
    "DeviceNotFoundError",
    "PatchPhaseError",
    "ResetpropError",
    "ProfileForgeError",
    "InjectionError",
    "WalletProvisionError",
    "GAppsBootstrapError",
]
