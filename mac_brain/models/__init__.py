from .local_detector import LocalNeuralObjectDetector
from .object_detection import Detection, DeterministicObjectDetector, ObjectDetector

# Compatibility exports for the existing Mac model provider implementation.
# `models.py` remains the canonical runtime/provider implementation for now.
from mac_brain.models_legacy import CallableMacBackend, MacModelProvider, MacModelSpec

__all__ = [
    "CallableMacBackend",
    "Detection",
    "DeterministicObjectDetector",
    "LocalNeuralObjectDetector",
    "MacModelProvider",
    "MacModelSpec",
    "ObjectDetector",
] 
