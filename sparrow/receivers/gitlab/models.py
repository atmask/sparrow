
from .enum import *
from dataclasses import dataclass

@dataclass
class GitlabUser:
    id: int
    name: str 
    username: str
    email: str

@dataclass
class GitlabProject:
    id: int
    name: str
    web_url: str
    namespace: str
    git_http_url: str

@dataclass 
class GitlabRepository:
    name: str
    url: str
    homepage: str

@dataclass
class GitlabLastCommit:
    sha: str

@dataclass
class GitlabMergeRequest:
    id: int
    iid: int
    target_branch: str
    source_branch: str
    last_commit: GitlabLastCommit
    action: GitlabMergeRequestAction = None

    def __post_init__(self):
        if not self.action:
            self.action = GitlabMergeRequestAction.NONE
        # self.last_commit = GitlabLastCommit(**self.last_commit)

@dataclass
class GitlabComment:
    id: int
    comment: str
    noteable_type: GitlabCommentType
   
@dataclass
class GitlabWebhookEvent:
    event_type: GitlabWebookEventType
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    
    # def __post_init__(self):
    #     self.user = GitlabUser(**self.user)
    #     self.project = GitlabProject(**self.project)
    #     self.repository = GitlabRepository(**self.repository)

@dataclass
class MergeRequestEvent(GitlabWebhookEvent):
    object_attributes: GitlabMergeRequest

    # def __post_init__(self):
    #     self.object_attributes = GitlabMergeRequest(**self.object_attributes)

@dataclass
class CommentEvent(GitlabWebhookEvent):
    object_attributes: GitlabComment
    
    # def __post_init__(self):
    #     self.object_attributes = GitlabComment(**self.object_attributes)

@dataclass
class MergeRequestCommentEvent(CommentEvent):
    merge_request: GitlabMergeRequest

    # def __post_init__(self):
    #     self.merge_request = GitlabMergeRequest(**self.merge_request)
