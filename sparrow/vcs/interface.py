from abc import abstractmethod
from sparrow.vcs.models import MergeRequestDiff
from typing import List
from sparrow.receivers.events import PullRequestEvent

class IVersionControlSystem:
    
    @abstractmethod
    def acknowledgeEvent(self, event: PullRequestEvent):
        '''Acknowledge that the event has been received and is being processed'''
        ...

    @abstractmethod
    def getChanges(self, event: PullRequestEvent) -> List[MergeRequestDiff]:
        '''Return a list of MergeRequestDiff objects which represent the old new paths of changed files'''
        ...

    @abstractmethod
    def cloneRepoAtSha(self, event: PullRequestEvent) -> str:
        '''
        Clone the repo for which this event is taking place at the sha. 
        Return the path to the locally cloned repo
        '''
        ...

    @abstractmethod 
    def postComment(self, event: PullRequestEvent, comment: str):
            """
            Posts a comment on a pull request event.

            Args:
                event (PullRequestEvent): The pull request event object.
                comment (str): The comment to be posted.

            Returns:
                None
            """
            
            ...

    @abstractmethod
    def postDiffComment(self, diffs):
        ...