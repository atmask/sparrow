from abc import abstractmethod
from sparrow.vcs.models import MergeRequestDiff
from typing import List
class IReleaseManager:

    @abstractmethod
    def generateDiff(self, chart_path: str, release_name: str, namespace: str, values_files: List[str]) -> str:
        ...
    
    @abstractmethod
    def performUpgradeOrInstall(self,  chart_path: str, release_name: str, namespace: str, values_files: List[str]) -> str:
        ...

    @abstractmethod
    def _ensureVersion(self):
        ...
    
    @abstractmethod
    def _installVersion(self):
        ...
    
    @abstractmethod
    def detectChangedReleases(self, repo_path: str, diffs: List[MergeRequestDiff]) -> List[str]:
        ...