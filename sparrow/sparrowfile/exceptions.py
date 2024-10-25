

class ClusterNotDefinedError(Exception):
    def __init__(self, cluster_name):
        self.cluster_name = cluster_name

    def __str__(self):
        return f"Cluster '{self.cluster_name}' is not defined"