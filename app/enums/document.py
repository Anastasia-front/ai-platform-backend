from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    INDEXED = "indexed"
    FAILED = "failed"
