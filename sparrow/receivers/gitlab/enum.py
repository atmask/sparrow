from enum import StrEnum

class GitlabMergeRequestAction(StrEnum):
    OPENED = "open"
    CLOSED = "close"
    REOPEN = "reopen"
    UPDATE = "update"
    APPROVED = "approved"
    UNAPPROVED = "unapproved"
    APPROVAL = "approval"
    UNAPPROVAL = "unapproval"
    MERGE = "merge"
    NONE = "none"

class GitlabWebookEventType(StrEnum):
    MERGE_REQUEST = "merge_request"
    NOTE = "note"
    EMOJI = "award"
    ISSUE = "issue"
    CONFIDENTIAL_NOTE = "confidential_note"

class GitlabCommentType(StrEnum):
    MERGE_REQUEST = "MergeRequest"
    COMMIT = "Commit"
    ISSUE = "Issue"
    SNIPPET = "Snippet"