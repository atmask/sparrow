from sparrow.cloudproviders.interface import ICloudProvider
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.containerservice import ContainerServiceClient
from sparrow.cloudproviders.decorators import handle_auth_exceptions

from sparrow.settings import AZURE_SUBSCRIPTION_ID
from sparrow.logger import logger
import logging

# Turn off noisy azure info logs
logging.getLogger('azure').setLevel(logging.WARNING)


class AzureClient(ICloudProvider):
    def __init__(self):
        self._client = self._authenticate()

    @handle_auth_exceptions
    def _authenticate(self):
        """Authenticate the client"""
        # Create a DefaultAzureCredential object to authenticate
        credential = DefaultAzureCredential()
        # Create a ContainerServiceClient client object and return
        return ContainerServiceClient(credential, AZURE_SUBSCRIPTION_ID)

    @handle_auth_exceptions
    def getKubeConfig(self, resource_group_name, cluster_name) -> str:
        """Get the raw kubeconfig for the AKS cluster"""
        logger.info(f"Getting kubeconfig for cluster: {cluster_name} in rg: {resource_group_name}")
        # Get the kubeconfig for the AKS cluster
        kubeconfig = self._client.managed_clusters.list_cluster_admin_credentials(
            resource_group_name, cluster_name).kubeconfigs[0].value

        return kubeconfig.decode('utf-8')

