"""Backward-compat shim — MAC_BRAIN is retired, use `brain`.

This module re-exports from `brain` so existing `from MAC_BRAIN.xxx import` code
keeps working during the migration. New code should import from `brain`.
"""
import warnings
warnings.warn("MAC_BRAIN is deprecated — import from brain instead", DeprecationWarning, stacklevel=2)

from brain.engine import Brain, BrainConfig, MacBrain, MacBrainConfig  # noqa: F401
try:
    from brain import *  # noqa: F401,F403
except Exception:
    pass

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
import types


class _MacBrainRedirectFinder(importlib.abc.MetaPathFinder):
    """Redirect any `MAC_BRAIN.xxx` import to `brain.xxx`."""

    def find_spec(self, fullname, path, target=None):  # type: ignore[override]
        if fullname == "MAC_BRAIN" or fullname.startswith("MAC_BRAIN."):
            brain_name = "brain" + fullname[len("MAC_BRAIN"):]
            try:
                spec = importlib.util.find_spec(brain_name)
                if spec is not None:
                    # Return a spec that loads brain_name but registers as fullname
                    loader = spec.loader
                    new_spec = importlib.machinery.ModuleSpec(fullname, loader, origin=spec.origin)
                    if spec.submodule_search_locations is not None:
                        new_spec.submodule_search_locations = list(spec.submodule_search_locations)
                    return new_spec
            except Exception:
                return None
        return None

    def invalidate_caches(self) -> None:
        return None

# Install at front so it wins over default finders
if not any(isinstance(f, _MacBrainRedirectFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _MacBrainRedirectFinder())

# Also pre-populate common submodules so `import MAC_BRAIN.storage` finds it in sys.modules immediately
# (helps cases where finder race or already-imported state)
try:
    import pkgutil
    import brain as _brain_pkg
    for mod in pkgutil.iter_modules(_brain_pkg.__path__, prefix="brain."):
        mac_name = "MAC_BRAIN" + mod.name[len("brain"):]
        if mac_name not in sys.modules:
            try:
                sys.modules[mac_name] = importlib.import_module(mod.name)
            except Exception:
                pass
    # Also brain.models.*
    try:
        import brain.models as _models_pkg
        for mod in pkgutil.iter_modules(_models_pkg.__path__, prefix="brain.models."):
            mac_name = "MAC_BRAIN" + mod.name[len("brain"):]
            if mac_name not in sys.modules:
                try:
                    sys.modules[mac_name] = importlib.import_module(mod.name)
                except Exception:
                    pass
    except Exception:
        pass
except Exception:
    pass


def __getattr__(name: str):  # PEP 562 — `MAC_BRAIN.storage` as attribute
    try:
        return importlib.import_module(f"brain.{name}")
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
