
from .gitlab.receiver import GitlabReceiver
from .interface import IReceiver

def ReceiverFactory(*args, **kwargs) -> IReceiver:
    if base_url := kwargs.get("base_url"):
        return _baseURLFactory(base_url)
    elif headers := kwargs.get(headers):
        return _headerFactory(headers)
    else:
        raise ValueError("Invalid args for ReceiverFactor. Expected \"base_url\" or \"headers\" param.")
    

## Parse based on the base url of the configured VCSProvider
def _baseURLFactory(base_url) -> IReceiver:
    if 'gitlab' in base_url:
        return GitlabReceiver()
    else:
        raise ValueError("Unsupported webhook.")

## TODO: If we support multiple recievers then parse based on incmoing header
def _headerFactory(headers) -> IReceiver:
    if headers.get(GitlabReceiver.HEADER):
        return GitlabReceiver()
    else:
        raise ValueError("Unsupported webhook.")