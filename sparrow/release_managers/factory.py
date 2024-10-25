
from sparrow.release_managers.helm.manager import Helm

def ReleaseManagerFactory(name: str, version: str, bin_path: str):
    match name.lower():
        case "helm":
            return Helm(version=version, bin_path=bin_path)
        case _:
            raise ValueError(f"Invalid release manager: {name}")