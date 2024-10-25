from contextlib import contextmanager
from dataclasses import dataclass
from abc import abstractmethod
from typing import List, Optional
from enum import StrEnum
import yaml

from sparrow.cloudproviders.azure.client import AzureClient
from sparrow.settings import SPARROW_KUBECONFIG_DIR
from sparrow.machine import system
import logging

from sparrow.sparrowfile.exceptions import ClusterNotDefinedError

logger  = logging.getLogger(__name__)

class ClusterProviderType(StrEnum):
    LOCAL = 'local'
    AZURE = 'azure'

@dataclass
class ClusterProvider:

    @abstractmethod
    @contextmanager
    def authenticate(self):
        """Autheticate to the cluster"""
        pass

@dataclass
class LocalCluster(ClusterProvider):
    kubeconfig: str

@dataclass
class AzureCluster(ClusterProvider):
    cluster_name: str
    resource_group: str

    @contextmanager
    def authenticate(self):
        if not self.resource_group or not self.cluster_name:
            raise ValueError("Resource Group and Cluster Name must be provided to authenticate to an Azure Cluster")
        
        ## Enter the conext manager for the cluster
        kubeconfig = AzureClient().getKubeConfig(self.resource_group, self.cluster_name)

        kubeconfig_dir = f'{SPARROW_KUBECONFIG_DIR}/{self.resource_group}'
        kubeconfig_file = f'{kubeconfig_dir}/{self.cluster_name}.yaml'

        if system.file_exists(kubeconfig_file):
            logger.debug(f"Removing existing kubeconfig file: {kubeconfig_file}")
            system.remove_file(kubeconfig_file)

        ## Create the directory if it does not exist
        system.create_dir(kubeconfig_dir)

        # Store the kubeconfig to a file
        with open(kubeconfig_file, 'w') as file:
            file.write(kubeconfig)

        # Set file permissions to read and write only for the current user
        system.set_file_permissions(kubeconfig_file, 0o600)
        
        ## Set the KUBECONFIG env variable
        system.set_env_var('KUBECONFIG', kubeconfig_file)
        
        try:
            ## Allow the context to run
            yield 
        finally:
            ## Remove the env var and file
            system.unset_env_var('KUBECONFIG')
            system.remove_file(kubeconfig_file)

@dataclass
class Cluster:
    name: str
    provider: ClusterProviderType
    provider_config: ClusterProvider


@dataclass
class ChartEnvironment:
    name: str
    valuesFiles: List[str]
    cluster: Cluster
    namespace: Optional[str] = None


@dataclass
class ChartConfiguration:
    path: str
    environments: List[ChartEnvironment]
    release_name: Optional[str] = None

    def get_environment(self, name: str) -> Optional[ChartEnvironment]:
        for env in self.environments:
            if env.name == name:
                return env
        return None

@dataclass
class SparrowFile:
    clusters: List[Cluster]
    chartConfigurations: List[ChartConfiguration]

    def _getChartNamespace(self, chart_path: str) -> str:
        '''Load the yaml file Chart.yaml at chart_path/Chart.yaml get the namespace key'''
        yaml_file = f'{chart_path}/Chart.yaml'
        if not system.file_exists(yaml_file):
            raise FileNotFoundError(f"Could not find the Chart.yaml file at {yaml_file}")
        
        with open(yaml_file, 'r') as file:
            chart_data = yaml.safe_load(file)
            return chart_data.get('namespace', 'default')
        
    def _getChartReleaseName(self, chart_path: str) -> str:
        '''Load the yaml file Chart.yaml at chart_path/Chart.yaml get the releaseName key'''
        yaml_file = f'{chart_path}/Chart.yaml'
        if not system.file_exists(yaml_file):
            raise FileNotFoundError(f"Could not find the Chart.yaml file at {yaml_file}")
        
        with open(yaml_file, 'r') as file:
            chart_data = yaml.safe_load(file)
            release_name = chart_data.get('releaseName')
            if not release_name:
                release_name = chart_data.get('name')
            return release_name
        
    def getChartConfiguration(self, chart_path: str) -> ChartConfiguration:
        chart_config = None
        greatest_match_length = -1
        for config in self.chartConfigurations:
            if match_length := system.path_match_length(config.path, chart_path) > greatest_match_length:
                chart_config = config
                greatest_match_length = match_length
        
        if chart_config:
            chart_config.release_name = self._getChartReleaseName(chart_path)
            chart_namespace = self._getChartNamespace(chart_path)
            for env in chart_config.environments:
                if env.namespace is None:
                    env.namespace = chart_namespace
        else:
            logger.info(f"No chart configuration found for chart at {chart_path}")
    
        return chart_config

    
    @staticmethod
    def _parse_clusters(yaml_data: dict) -> List[Cluster]:
        clusters = []
        for cluster_data in yaml_data.get('clusters', []):
            name = cluster_data.get('name')
            provider_type = ClusterProviderType(cluster_data.get('provider', ''))
            provider_config = None

            if provider_type == ClusterProviderType.LOCAL:
                provider_config = LocalCluster(kubeconfig=cluster_data.get('providerConfig', {}).get('kubeconfig', ''))
            elif provider_type == ClusterProviderType.AZURE:
                logger.info(f"Cluster Data in parse clusters: {cluster_data}")
                provider_config = AzureCluster(
                    cluster_name=cluster_data.get('providerConfig', {}).get('clusterName', ''),
                    resource_group=cluster_data.get('providerConfig', {}).get('resourceGroup', '')
                )
                logger.info(f"Cluster Provider Config in parse clusters: {provider_config}")

            cluster = Cluster(name=name, provider=provider_type, provider_config=provider_config)
            clusters.append(cluster)
        return clusters

    @staticmethod
    def _parse_chart_configurations(yaml_data: dict, clusters: List[Cluster]) -> List[ChartConfiguration]:
        chartConfigurations = []
        for chart_config_data in yaml_data.get('chartConfigurations', []):
            path = chart_config_data.get('path')
            environments = []
            for env in chart_config_data.get('environments', []):
                name = env.get('name')
                valuesFiles = env.get('valuesFiles', [])
                cluster_name = env.get('cluster')
                namespace = env.get('namespace')
                cluster = None
                for c in clusters:
                    if c.name == cluster_name:
                       cluster = c
                
                if cluster is None:
                    raise ClusterNotDefinedError(cluster_name)
                
                environments.append(ChartEnvironment(name=name, valuesFiles=valuesFiles, cluster=cluster, namespace=namespace))
            
            chartConfigurations.append(ChartConfiguration(path=path, environments=environments))
        return chartConfigurations
    

    @classmethod
    def from_yaml(cls, yaml_file: str) -> 'SparrowFile':
        if not system.file_exists(yaml_file):
            raise FileNotFoundError(f"Could not find the Sparrowfile at {yaml_file}")
        
        try:
            with open(yaml_file, 'r') as file:
                yaml_data = yaml.safe_load(file)

            clusters = cls._parse_clusters(yaml_data)
            chartConfigurations = cls._parse_chart_configurations(yaml_data, clusters)
        except Exception as e:
            raise e

        return SparrowFile(clusters=clusters, chartConfigurations=chartConfigurations)