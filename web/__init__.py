"""Backward-compat shim — `web` is now `novi.web`."""
import warnings
warnings.warn("web is deprecated — import from novi.web instead", DeprecationWarning, stacklevel=2)
import importlib, importlib.abc, importlib.machinery, importlib.util, pkgutil, sys
try:
    import novi.web as _real
    sys.modules.setdefault("web", _real)
    for mod in pkgutil.iter_modules(_real.__path__, prefix="novi.web."):
        wname = "web" + mod.name[len("novi.web"):]
        if wname not in sys.modules:
            try:
                sys.modules[wname] = importlib.import_module(mod.name)
            except Exception:
                pass
except Exception:
    pass
class _WebRedirectFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "web" or fullname.startswith("web."):
            novi_name = "novi." + fullname
            if fullname in sys.modules:
                return importlib.machinery.ModuleSpec(fullname, loader=None)
            try:
                mod = importlib.import_module(novi_name)
                sys.modules[fullname] = mod
                return importlib.machinery.ModuleSpec(fullname, loader=None)
            except Exception:
                return None
        return None
if not any(isinstance(f, _WebRedirectFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _WebRedirectFinder())
def __getattr__(name: str):
    try:
        return importlib.import_module(f"novi.web.{name}")
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
