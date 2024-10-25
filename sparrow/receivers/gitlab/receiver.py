from sparrow.receivers.interface import IReceiver
from sparrow.receivers.gitlab import enum
from sparrow.receivers.gitlab.schema import (
    GitlabWebhookEventSchema, 
    MergeRequestEventSchema, 
    CommentEventSchema,
    MergeRequestCommentEventSchema,
)
from sparrow.receivers.gitlab import models
from marshmallow import ValidationError
from sparrow.receivers.events import PullRequestEvent, PullRequestEventType, MergeRequest, Repo
from sparrow.logger import logger
from sparrow.receivers.models import Comment


class GitlabReceiver(IReceiver):
    HEADER = "X-Gitlab-Event"
    
    def getEvent(self, request_json: dict) -> PullRequestEvent:
        '''
        Process the gitlab webhook event according to schema and return a standard PullRequestEvent
        '''
        try:
            webhook_event: models.GitlabWebhookEvent = GitlabWebhookEventSchema().load(request_json)
        except ValidationError as e:
            raise Exception(f"Failed to deserialize Gitlab base webhook event: {e}")
        
        logger.info(f"event: {webhook_event}")
        match webhook_event.event_type:
            case enum.GitlabWebookEventType.MERGE_REQUEST:
                try:
                    webhook_event: models.MergeRequestEvent = MergeRequestEventSchema().load(request_json)
                except ValidationError as e:
                    raise Exception(f"Failed to deserialize Gitlab Merge Request Event: {e}")

                ## Don't care about approval changes, etc.
                if not (pr_event_type := self._getMergeRequestEventSchemaType(webhook_event.object_attributes.action)):
                    logger.warning(f"Unsupported merge request action {webhook_event.object_attributes.action}. Ignoring this event...")
                    return None
                
                mr = MergeRequest(
                    id = webhook_event.object_attributes.iid,
                    sha=webhook_event.object_attributes.last_commit.sha,
                    ref_name=webhook_event.object_attributes.source_branch
                )

                repo = Repo(
                    id = webhook_event.project.id,
                    http_clone_url=webhook_event.project.git_http_url
                )

                return PullRequestEvent(
                    repo=repo,
                    user=webhook_event.user.id,
                    type=pr_event_type,
                    mr=mr
                )
            
            case enum.GitlabWebookEventType.NOTE:
                try:
                    webhook_event: models.CommentEvent = CommentEventSchema().load(request_json)
                except ValidationError as e:
                    raise Exception(f"Failed to deserialize Gitlab Base Comment Event: {e}")

                ## We only care about comments on open merge requests
                if webhook_event.object_attributes.noteable_type != enum.GitlabCommentType.MERGE_REQUEST:
                    return None

                ## Get MR Comment
                try:
                    webhook_event: models.MergeRequestCommentEvent = MergeRequestCommentEventSchema().load(request_json)
                except ValidationError as e:
                    raise Exception(f"Failed to deserialize Gitlab MR Comment Event: {e}")

                ## Get the comment command if one exists
                command = Comment(webhook_event.object_attributes.comment).parseCommand()
                if not command.type:
                    logger.debug(f"Comment was not a command to Sparrow and no close suggestion was found. Ignoring this comment...")
                    return None
                
                mr = MergeRequest(
                    id = webhook_event.merge_request.iid,
                    sha=webhook_event.merge_request.last_commit.sha,
                    ref_name=webhook_event.merge_request.source_branch
                )

                repo = Repo(
                    id = webhook_event.project.id,
                    http_clone_url=webhook_event.project.git_http_url
                )
                
                # include suggestion and comment id
                return PullRequestEvent(
                    repo=repo,
                    user=webhook_event.user.id,
                    type=command.type,
                    mr=mr,
                    comment_id=webhook_event.object_attributes.id,
                    command=command
                )

            case _:
                logger.warning(f"Unsupported Gitlab Webhook Event: {webhook_event.event_type}. Not Processing...")
                return None


    def _getMergeRequestEventSchemaType(self, action: enum.GitlabMergeRequestAction) -> enum.GitlabWebookEventType:
        '''
        Map the GitlabMergeRequestActions to a PullRequestEventType. Return None if not a watched event
        '''
        match action:
            case (enum.GitlabMergeRequestAction.OPENED | enum.GitlabMergeRequestAction.REOPEN):
                return PullRequestEventType.MR_OPENED
            case enum.GitlabMergeRequestAction.CLOSED:
                return PullRequestEventType.MR_CLOSED
            case enum.GitlabMergeRequestAction.UPDATE:
                return PullRequestEventType.MR_MODIFIED
            case _:
                return None

