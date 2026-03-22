"""
CareCompanion — Billing Engine Detectors Package

Each module in this package contains one or more detector classes
inheriting from BaseDetector. The BillingCaptureEngine auto-discovers
all BaseDetector subclasses at startup.
"""

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)


def discover_detector_classes():
    """
    Auto-discover all BaseDetector subclasses in this package.

    Imports every module in billing_engine/detectors/ and collects
    all classes that inherit from BaseDetector (excluding BaseDetector itself).

    Returns
    -------
    list of BaseDetector subclasses (not instantiated)
    """
    from billing_engine.base import BaseDetector

    classes = []
    package_path = __path__
    package_name = __name__

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        try:
            module = importlib.import_module(f"{package_name}.{module_name}")
        except Exception:
            logger.warning("Failed to import detector module: %s", module_name,
                           exc_info=True)
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, BaseDetector)
                    and attr is not BaseDetector
                    and attr.CATEGORY):
                classes.append(attr)

    return classes
