
from .receivers.interface import IReceiver
from .receivers.factory import ReceiverFactory
from .vcs.interface import IVersionControlSystem
from .vcs.factory import VCSProviderFactory
from .release_managers.interface import IReleaseManager
from .settings import VCS_BASE_URL, VCS_TOKEN, SPARROW_ROOT_PATH, HELM_VERSION, SPARROW_CLONE_DIR, BINARY_PATH, BASIC_AUTH_ENABLED, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD
from .release_managers.factory import ReleaseManagerFactory
from sparrow.machine import system

## Define the config object that will be used by the controller
class SparrowConfig:
    def __init__(self, receiver: IReceiver, vcs: IVersionControlSystem, release_manager: IReleaseManager, server_path_prefix: str):
        self.receiver = receiver
        self.vcs = vcs
        self.release_manager = release_manager
        self.server_path_prefix = server_path_prefix

## Add the binary path to the global path
if not system.is_in_path(BINARY_PATH):
    system.add_to_path(BINARY_PATH)

## Get instances for injection
vcs_provider: IVersionControlSystem = VCSProviderFactory(base_url=VCS_BASE_URL, token=VCS_TOKEN, working_dir=SPARROW_CLONE_DIR)
receiver: IReceiver = ReceiverFactory(base_url=VCS_BASE_URL)
release_manager = ReleaseManagerFactory(name="helm", version=HELM_VERSION, bin_path=BINARY_PATH)

## Inject dependencies
DefaultConfig = SparrowConfig(receiver, vcs_provider, release_manager, SPARROW_ROOT_PATH)