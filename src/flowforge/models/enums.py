from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class JobType(StrEnum):
    DATA_PREPARATION = "data_preparation"
    MODEL_INFERENCE = "model_inference"
    REPORT_GENERATION = "report_generation"
    FILE_PROCESSING = "file_processing"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ModelStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class OutputKind(StrEnum):
    JSON = "json"
    FILE = "file"
    REPORT = "report"
    PREDICTION = "prediction"

