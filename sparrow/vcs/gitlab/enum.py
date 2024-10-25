from enum import StrEnum

class CommitState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"

class CommitStatusName(StrEnum):
    DIFF = "Sparrow/diff"
    APPLY = "Sparrow/apply"

class CommitStatusDescription(StrEnum):
    DIFF = "Generating Diff"
    APPLY = "Applying Changes"