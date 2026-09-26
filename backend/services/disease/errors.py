"""Structured, user-safe error codes (never raw exceptions to clients).

Two families share this module:
- error codes: something failed in transport/validation/infra.
- reason codes: machine-readable explanation of an analysis outcome,
  including healthy non-diagnosis states (e.g. NO_ELIGIBLE_SPECIALIST
  means "routing correctly found no model", never "a model broke").
"""

IMAGE_INVALID = "IMAGE_INVALID"
IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
IMAGE_POOR_QUALITY = "IMAGE_POOR_QUALITY"
NO_VALID_MODEL = "NO_VALID_MODEL"
MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
MODEL_INFERENCE_FAILED = "MODEL_INFERENCE_FAILED"
INFERENCE_TIMEOUT = "INFERENCE_TIMEOUT"
VLM_UNAVAILABLE = "VLM_UNAVAILABLE"
KNOWLEDGE_UNAVAILABLE = "KNOWLEDGE_UNAVAILABLE"
UNSUPPORTED_CROP = "UNSUPPORTED_CROP"
SYSTEM_ERROR = "SYSTEM_ERROR"

# Reason codes attached to (usually HTTP-200) analysis results.
NO_ELIGIBLE_SPECIALIST = "NO_ELIGIBLE_SPECIALIST"
NO_VERIFIED_MODEL_FOR_CROP = "NO_VERIFIED_MODEL_FOR_CROP"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
SPECIALIST_DISAGREEMENT = "SPECIALIST_DISAGREEMENT"
POOR_IMAGE_QUALITY = "POOR_IMAGE_QUALITY"


class DiseaseError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
