"""Module registry for hot-pluggable components."""

from __future__ import annotations

import threading
from typing import Any

from fastrs.core.types import ModuleInfo, ModuleType
from fastrs.log import get_logger

logger = get_logger(__name__)


class ModuleRegistry:
    """Thread-safe registry for dynamically managing pipeline modules.

    Supports hot-plug: modules can be registered, unregistered, enabled,
    and disabled at runtime without restarting the server.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._modules: dict[str, dict[str, Any]] = {}

    # -- registration ----------------------------------------------------------

    def register(self, name: str, module_type: ModuleType, instance: Any, *, description: str = "") -> None:
        """Register a module instance.

        Raises:
            ValueError: If a module with the same name is already registered.
        """
        with self._lock:
            if name in self._modules:
                raise ValueError(f"Module '{name}' is already registered")
            self._modules[name] = {
                "instance": instance,
                "info": ModuleInfo(name=name, module_type=module_type, enabled=True, description=description),
            }
            logger.info("module_registered", name=name, module_type=module_type.value)

    def unregister(self, name: str) -> None:
        """Remove a module from the registry.

        Raises:
            KeyError: If the module is not found.
        """
        with self._lock:
            if name not in self._modules:
                raise KeyError(f"Module '{name}' not found")
            del self._modules[name]
            logger.info("module_unregistered", name=name)

    # -- enable / disable ------------------------------------------------------

    def enable(self, name: str) -> None:
        """Enable a registered module."""
        with self._lock:
            self._get_entry(name)["info"].enabled = True
            logger.info("module_enabled", name=name)

    def disable(self, name: str) -> None:
        """Disable a registered module (remains registered but inactive)."""
        with self._lock:
            self._get_entry(name)["info"].enabled = False
            logger.info("module_disabled", name=name)

    # -- restart (replace instance) --------------------------------------------

    def restart(self, name: str, new_instance: Any) -> None:
        """Replace the instance of a registered module (hot-swap)."""
        with self._lock:
            entry = self._get_entry(name)
            entry["instance"] = new_instance
            logger.info("module_restarted", name=name)

    # -- query -----------------------------------------------------------------

    def get(self, name: str) -> Any:
        """Return the instance of a registered module."""
        with self._lock:
            return self._get_entry(name)["instance"]

    def get_info(self, name: str) -> ModuleInfo:
        """Return metadata about a registered module."""
        with self._lock:
            return self._get_entry(name)["info"]

    def list_modules(self, module_type: ModuleType | None = None, *, enabled_only: bool = False) -> list[ModuleInfo]:
        """List registered modules, optionally filtered."""
        with self._lock:
            results: list[ModuleInfo] = []
            for entry in self._modules.values():
                info: ModuleInfo = entry["info"]
                if module_type is not None and info.module_type != module_type:
                    continue
                if enabled_only and not info.enabled:
                    continue
                results.append(info)
            return results

    def get_instances(self, module_type: ModuleType, *, enabled_only: bool = True) -> dict[str, Any]:
        """Return {name: instance} mapping for modules of a given type."""
        with self._lock:
            result: dict[str, Any] = {}
            for name, entry in self._modules.items():
                info: ModuleInfo = entry["info"]
                if info.module_type != module_type:
                    continue
                if enabled_only and not info.enabled:
                    continue
                result[name] = entry["instance"]
            return result

    # -- internals -------------------------------------------------------------

    def _get_entry(self, name: str) -> dict[str, Any]:
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found")
        return self._modules[name]
