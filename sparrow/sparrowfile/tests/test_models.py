from sparrow.sparrowfile.models import SparrowFile, Cluster
import pytest
import os
from unittest.mock import patch, Mock

class TestSparrowFileAzure():

    @pytest.fixture
    def azure_sparrowfile_path(self):
        crdir = os.getcwd()
        return f'{crdir}/sparrow/sparrowfile/tests/data/sparrowfile_azure.yaml'

    def test_from_yaml(self, azure_sparrowfile_path):
        """
        Test case for the `from_yaml` method of the `SparrowFile` class.
        It verifies that the `from_yaml` method correctly parses a YAML file and creates a `SparrowFile` object with the expected clusters and chart configurations.

        Args:
            azure_sparrowfile_path (str): The path to the Azure Sparrowfile YAML file.

        Returns:
            None
        """

        sparrowfile = SparrowFile.from_yaml(azure_sparrowfile_path)
        assert len(sparrowfile.clusters) == 2

        expected_clusters = [
            {'name': 'dev-cluster', 
             'provider': 'azure', 
             'providerConfig':{
                    'clusterName': 'dev-cluster', 
                    'resourceGroup': 'dev-cluster-rg'
                },
            },
            {
                'name': 'test-cluster',
                'provider': 'azure',
                'providerConfig': {
                    'clusterName': 'test-cluster',
                    'resourceGroup': 'test-cluster-rg'
                }
            }
        ]
        for cluster, expected_clusters in zip(sparrowfile.clusters, expected_clusters):
            assert cluster.name == expected_clusters['name']
            assert cluster.provider == expected_clusters['provider']
            assert cluster.provider_config.cluster_name == expected_clusters['providerConfig']['clusterName']
            assert cluster.provider_config.resource_group == expected_clusters['providerConfig']['resourceGroup']
        
        expected_chart_configs = [
            {
                'path': 'clusters/softwareTeam/',
                'environments': [
                    {
                        'name': 'dev',
                        'valuesFiles': ['values-dev.yaml'],
                        'cluster': 'dev-cluster',
                    },
                    {
                        'name': 'test',
                        'valuesFiles': ['values-test.yaml'],
                        'cluster': 'test-cluster',
                    }
                ]
            }
        ]

        assert len(sparrowfile.chartConfigurations) == len(expected_chart_configs)
        for chart_config, expected_chart_configs in zip(sparrowfile.chartConfigurations, expected_chart_configs):
            assert chart_config.path == expected_chart_configs['path']

            assert len(chart_config.environments) == len(expected_chart_configs['environments'])
            for env, expected_env in zip(chart_config.environments, expected_chart_configs['environments']):
                assert env.name == expected_env['name']
                assert env.valuesFiles == expected_env['valuesFiles']
                assert env.cluster.name == expected_env['cluster']
                assert env.namespace == None
    
    def test_getChartConfiguration(self, azure_sparrowfile_path):
        """
        Test case for the `getChartConfiguration` method of the SparrowFile class.

        This test verifies that the `getChartConfiguration` method returns the correct chart configuration
        for a given chart path.

        Args:
            azure_sparrowfile_path (str): The path to the Azure Sparrowfile.

        Returns:
            None
        """
        sparrowfile = SparrowFile.from_yaml(azure_sparrowfile_path)
        with patch('sparrow.sparrowfile.models.SparrowFile._getChartNamespace') as mock_getChartNamespace:
            mock_getChartNamespace.return_value = 'default'
            
            chart_config = sparrowfile.getChartConfiguration('clusters/softwareTeam/chartA')
            assert chart_config.path == 'clusters/softwareTeam/'

            assert len(chart_config.environments) == 2
            for env in chart_config.environments:
                assert isinstance(env.cluster, Cluster)
                assert env.namespace == 'default'
                if env.cluster.name == 'dev-cluster':
                    assert env.name == 'dev'
                    assert env.valuesFiles == ['values-dev.yaml']
                elif env.cluster.name == 'test-cluster':
                    assert env.name == 'test'
                    assert env.valuesFiles == ['values-test.yaml']
                else:
                    assert False, "Unexpected cluster name"
            


        