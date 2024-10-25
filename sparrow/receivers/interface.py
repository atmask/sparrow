from .events import PullRequestEvent

class IReceiver:

    def getEvent(self) -> PullRequestEvent:
        pass