

from sparrow.vcs.interface import IVersionControlSystem
from sparrow.http.interface import IHTTPClient
from .enum import CommitState, CommitStatusName, CommitStatusDescription
from .models import GitlabPipeline
from sparrow.vcs.models import MergeRequestDiff
from .schema import MergeRequestDiff, PipelineSchema, CommitStatusBodySchema, EmojiBodySchema, NoteBodySchema
from .endpoints import ENDPOINTS
from sparrow.receivers.events import PullRequestEvent, PullRequestEventType, Repo
from marshmallow import ValidationError
from sparrow.logger import logger
import time
from typing import List
import git
from sparrow.machine import system

class GitlabConfig:
    def __init__(self, token: str, base_url: str="https://gitlab.com/"):
        self.token = token
        self.base_url = base_url

class GitlabVCS(IVersionControlSystem):
    AUTH_HEADER='Authorization'
    TOKEN_PREFIX='Bearer'
    API_VERSION='v4'

    def __init__(self, config: GitlabConfig, http_client: IHTTPClient, working_dir: str="/tmp"):
        self.http_client = http_client(
            auth_header=GitlabVCS.AUTH_HEADER, 
            auth_token=f"{GitlabVCS.TOKEN_PREFIX} {config.token}", 
            base_url=f"{config.base_url}/api/{GitlabVCS.API_VERSION}"
        )
        self.token = config.token
        self.working_dir = working_dir

    def postComment(self, event: PullRequestEvent, comment: str):
        return self._commentOnMergeRequest(project_id=event.repo.id, mr_iid=event.mr.id, comment=comment)

    def _commentOnMergeRequest(self, project_id: int, mr_iid: int, comment: str):
        endpoint = ENDPOINTS.get("projects").get("merge_requests").get("notes").get("base").format(project_id=project_id, mr_iid=mr_iid)
        try:
            payload = NoteBodySchema().dump(dict(body=comment))
        except ValidationError as e:
            raise Exception(f"Failed to serialize comment to be posted to mr: {e}")
        
        self.http_client.post(endpoint, body=payload)
        

    def _getLatestPipeline(self, project_id: str, ref_name: str) -> GitlabPipeline:
        endpoint = ENDPOINTS.get("projects").get("pipelines").get("latest").format(project_id=project_id, ref=ref_name)
        resp = self.http_client.get(endpoint)
        try:
            ret = PipelineSchema().load(resp.json)
        except ValidationError as e:
            logger.warning(f"Could not find any running pipelines for ref: {ref_name}. Returning None.")
            ret = None
        return ret
    
    def _getStatusMetadata(self, event_type: PullRequestEventType) -> tuple[CommitStatusName, CommitStatusDescription]:
        match event_type:
            case (PullRequestEventType.MR_OPENED | PullRequestEventType.COMMENT_DIFF | PullRequestEventType.MR_MODIFIED):
                return CommitStatusName.DIFF, CommitStatusDescription.DIFF
            case (PullRequestEventType.COMMENT_APPLY):
                return CommitStatusName.APPLY, CommitStatusDescription.APPLY
            case _:
                logger.warning(f"No valid commit status for this event: {event_type}")
                return None, None

    def _setCommitStatus(self, status: CommitState, project_id: str, sha: str, ref_name: str, event_type: PullRequestEventType):
        ## Don't fall into the same issue as:
        # https://github.com/runatlantis/atlantis/issues/3373
        # https://github.com/runatlantis/atlantis/issues/2484
        # https://github.com/runatlantis/atlantis/pull/2745/files/a2dd0a28bcb894ecf8c932d80bae17e5757a8741#diff-22d1bafb2e6e476aabe2f33484daa3f74932c6e0266f0830d7d948b8b9f60183
        # https://gitlab.com/gitlab-org/gitlab/-/issues/431660#note_1792942299
        
        # no good needs to be this sha
        pipeline = self._getLatestPipeline(project_id=project_id, ref_name=ref_name)

        name, desc = self._getStatusMetadata(event_type)
        if not name or not desc:
            raise Exception("No name or description for the status. Cannot update the mr status.")

        body = dict(
            pipeline_id=pipeline.id if pipeline else None,
            commit_state=status,
            name=name,
            description=desc,
        )
        endpoint = ENDPOINTS.get("projects").get("statuses").get("update").format(project_id=project_id, sha=sha)
        self.http_client.post(endpoint, body=CommitStatusBodySchema().dump(body))

    def _setCommitStatusRunning(self, project_id: str, sha: str, ref_name: str, event_type: PullRequestEventType):
        self._setCommitStatus(CommitState.RUNNING, project_id, sha, ref_name, event_type)
    
    def _setCommitStatusSucess(self, project_id: str, sha: str, ref_name: str, event_type: PullRequestEventType):
        self._setCommitStatus(CommitState.SUCCESS, project_id, sha, ref_name, event_type)
    
    def _setCommitStatusFailure(self, project_id: str, sha: str, ref_name: str, event_type: PullRequestEventType):
        self._setCommitStatus(CommitState.FAILED, project_id, sha, ref_name, event_type)
    
    def _setEmoji(self, project_id, mr_iid, comment_id: str, emoji="eyes"):
        endpoint = ENDPOINTS.get("projects").get("merge_requests").get("notes").get("react_emoji").format(project_id=project_id, mr_iid=mr_iid, note_id=comment_id)
        self.http_client.post(endpoint, body=EmojiBodySchema().dump(dict(name="eyes")))


    def acknowledgeEvent(self, event: PullRequestEvent):
        '''
        Acknowledge a recieved event to the user
        '''
        logger.info(f"ack event: {event.__dict__}")
        match event.type:
            case (PullRequestEventType.COMMENT_APPLY | PullRequestEventType.COMMENT_DIFF | PullRequestEventType.MR_OPENED | PullRequestEventType.MR_MODIFIED):
                logger.info("set status")
                self._setCommitStatusRunning(project_id=event.repo.id, sha=event.mr.sha, ref_name=event.mr.ref_name, event_type=event.type)
                
                ## React to new comments commands
                if event.type in [PullRequestEventType.COMMENT_APPLY, PullRequestEventType.COMMENT_DIFF]:
                    logger.info("set emoji")
                    self._setEmoji(project_id=event.repo.id, mr_iid=event.mr.id, comment_id=event.comment_id)
                return
            
            case PullRequestEventType.COMMENT_SUGGESTION:
                self._commentOnMergeRequest(project_id=event.repo.id, mr_iid=event.mr.id, comment=event.command.suggestion)
                return

            case _:
                logger.warning(f"Unrecognized event type: {event.type}. Not handling...")
                return
    
    def SetEventSuccess(self, event: PullRequestEvent):
        self._setCommitStatusSucess(project_id=event.repo.id, sha=event.mr.sha, ref_name=event.mr.ref_name, event_type=event.type)

    def SetEventFailure(self, event: PullRequestEvent):
        self._setCommitStatusFailure(project_id=event.repo.id, sha=event.mr.sha, ref_name=event.mr.ref_name, event_type=event.type)

    def getChanges(self, event: PullRequestEvent) -> List[MergeRequestDiff]:
        '''Return a list of MergeRequestDiff objects that represent the file changed. In particular the old path and new path of all modified files'''
        ## TODO: Add page checking
        endpoint = ENDPOINTS.get("projects").get("merge_requests").get("diffs").format(project_id=event.repo.id, mr_iid=event.mr.id)
        resp = self.http_client.get(endpoint)
        try:
            diffs = MergeRequestDiff(many=True).load(resp.json())
        except ValidationError as e:
            logger.warning(f"Could not deserialize the Gitlab diffs in project {event.repo.id} mr {event.mr.id}. Returning None. Exception: {e}")
            return None
        
        return diffs  
    
    def _authenticate_url(self, url: str):
        '''Authenticate an http git clone url with the token'''
        return url.replace("https://", f"https://oauth2:{self.token}@")

    def _get_local_repo_path(self, repo_id: Repo, sha: str):
        '''Return a path to the repo in the local environment that is unique to the repo and sha'''
        return system.join_paths(self.working_dir, f"{repo_id}-{sha}")

    def cloneRepoAtSha(self, event: PullRequestEvent) -> str:
        '''Clones a repo to the local working dir and returns the path to the repo'''

        git_http_url = event.repo.http_clone_url
        git_http_url = self._authenticate_url(git_http_url)

        local_repo_path = self._get_local_repo_path(event.repo.id, event.mr.sha)

        ## Check if there is a local repo-sha copy already
        if system.dir_exists(local_repo_path):
            logger.info(f"Local repo {local_repo_path} already exists. Skipping clone")
            return local_repo_path


        ## Clone repo into unique repo hash dir
        logger.info("Cloning repo...")

        repo: git.Repo = git.Repo.clone_from(git_http_url, local_repo_path, depth=1)

        ## Checkout the commit hash
        commit_hash = event.mr.sha
        logger.info(f"Checking out commit hash {commit_hash}...")
        repo.git.fetch('--depth', '1', 'origin', commit_hash)
        repo.git.checkout(commit_hash)

        return local_repo_path
        
                



    