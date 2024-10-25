import subprocess
import logging

logger = logging.getLogger(__name__)

class HelmDiff:
    
    @staticmethod
    def _ensureInstallation() -> bool:
        try:
            # Run the 'helm plugin list' command
            result = subprocess.run(['helm', 'plugin', 'list'], capture_output=True, text=True, check=True)
            # Check if the plugin name is in the output
            return 'diff' in result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error checking Helm plugins: {e}")
            return False    
    
    @classmethod
    def install(cls) -> None:
        if cls._ensureInstallation():
            return
        
        logger.debug("Installing Helm Diff plugin")
        try:
            subprocess.run(['helm', 'plugin', 'install', 'https://github.com/databus23/helm-diff'], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing Helm Diff plugin: {e}")
            raise e
        else:
            if cls._ensureInstallation():
                logger.info("Helm Diff plugin installed successfully")
            else:
                raise Exception("Helm Diff plugin could not be installed")

        


