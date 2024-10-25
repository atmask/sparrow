from enum import Enum
from typing import TypeAlias, List
from dataclasses import dataclass


## Define types
User: TypeAlias = str
Suggestion: TypeAlias = str


class PullRequestEventType(Enum):
    COMMENT_DIFF = 1
    COMMENT_APPLY = 2
    MR_OPENED = 3
    MR_MODIFIED = 4
    MR_CLOSED = 5
    COMMENT_SUGGESTION = 6 # If the input is close to a command but not valid post a suggestion

@dataclass
class MergeRequest:
    id: int
    sha: str
    ref_name: str

@dataclass
class Repo:
    id: int
    http_clone_url: str

@dataclass
class Command:
    type: PullRequestEventType
    suggestion: Suggestion
    flags: List[str]

class PullRequestEvent():
    def __init__(self, repo: Repo, user: User,  type: PullRequestEventType, mr: MergeRequest,command: Command = None, comment_id: int = None):
        self.repo = repo
        self.user = user
        self.command = command
        self.type = type
        self.mr = mr
        self.comment_id = comment_id