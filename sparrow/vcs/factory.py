from .gitlab.client import GitlabConfig, GitlabVCS
from .interface import IVersionControlSystem
from sparrow.http.http import AuthenticatedHTTPClient

def VCSProviderFactory(base_url: str, working_dir: str, *args, **kwargs) -> IVersionControlSystem:
    base_url = base_url.lower()
    if 'gitlab' in base_url:
        return GitlabVCS(GitlabConfig(token=kwargs.get("token"), base_url=base_url), http_client=AuthenticatedHTTPClient, working_dir=working_dir)
    elif 'github' in base_url:
        pass
    else:
        raise ValueError(f"Invalid Value for VCS Provider Factory. Provider for {base_url} not supported.")


