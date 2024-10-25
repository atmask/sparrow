
from sparrow.machine import system
from sparrow.machine import enum as machine_enum
from sparrow.logger import logger
from sparrow.release_managers.helm import enum, plugins
import subprocess
from sparrow.vcs.models import MergeRequestDiff
from typing import List


class Helm:
    BASE_INSTALL_URL = "https://get.helm.sh"

    def __init__(self, version, bin_path: str):
        self.version = version
        self.bin_path = bin_path
        self._installVersion()
        plugins.HelmDiff.install()

    def _getChartDependencies(self, chart_path: str) -> List[str]:
        '''Get the dependencies of a Helm chart'''
        cmd = ['helm', 'dependency', 'update', chart_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"Error getting dependencies for chart {chart_path}. Error: {stderr}")
            return False
        return True

    def generateDiff(self, chart_path: str, release_name: str, namespace: str, values_files: List[str]) -> str:
        try:
            if not self._getChartDependencies(chart_path):
                raise subprocess.CalledProcessError("Error getting chart dependencies")

            cmd=['helm', 'diff', 'upgrade', release_name, chart_path, '--allow-unreleased', '--namespace', namespace]
            for values_file in values_files:
                cmd.extend(['-f', f"{chart_path}/{values_file}"])
            
            logger.debug(f"Running diff command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
      
            # Capture stdout and stderr
            stdout_output, stderr_output = process.communicate()

            # # Join the output lists into strings
            stdout_output = ''.join(stdout_output).strip()
            stderr_output = ''.join(stderr_output).strip()
            
            logger.debug(f"Diff command output: {stdout_output}")
            logger.debug(f"Diff command error: {stderr_output}")

            if not stdout_output and not stderr_output:
                return "No changes for the chart in this environment were detected. Everything is up to date." 
            
            return stderr_output if stderr_output else stdout_output
        except subprocess.CalledProcessError as e:
            logger.error(f"Error generating diff: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating diff: {e}")
            return None
        
    def performUpgradeOrInstall(self, chart_path: str, release_name: str, namespace: str, values_files: List[str]) -> str:
        try:
            if not self._getChartDependencies(chart_path):
                raise subprocess.CalledProcessError("Error getting chart dependencies")

            cmd=['helm','upgrade', '-i', release_name, chart_path, '--dry-run', '--namespace', namespace]
            for values_file in values_files:
                cmd.extend(['-f', f"{chart_path}/{values_file}"])
            
            logger.debug(f"Running apply command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
      
            # Capture stdout and stderr
            stdout_output, stderr_output = process.communicate()

            # # Join the output lists into strings
            stdout_output = ''.join(stdout_output).strip()
            stderr_output = ''.join(stderr_output).strip()
            
            logger.debug(f"Apply command output: {stdout_output}")
            logger.debug(f"Apply command error: {stderr_output}")

            if not stdout_output and not stderr_output:
                return "" 
            
            return stderr_output if stderr_output else stdout_output
        except subprocess.CalledProcessError as e:
            logger.error(f"Error calling apply: {e}")
            return None
        except Exception as e:
            logger.error(f"Error running apply: {e}")
            return None

    def fileIsInChartDirectory(self, file_path, root_dir) -> str:
        '''Check if the file is in a Helm chart directory. If so return the root directory of the chart. Otherwise return None'''
        if file_path == '':
            return None
        
        if file_path == root_dir:
            ## Stop recursion
            return file_path if self.isHelmChartDirectory(file_path) else None
        
        ## Recurse up the directory tree
        if self.isHelmChartDirectory(file_path):
            return file_path
        else:
            return self.fileIsInChartDirectory(file_path=system.get_parent_dir(file_path), root_dir=root_dir)
    
    def isHelmChartDirectory(self, dir_path: str) -> bool :
        # Define required files and directories for a basic Helm chart
        required_files = ['Chart.yaml', 'chart.yaml']
        required_dirs = ['templates']

        logger.debug(f"Checking if {dir_path} is a helm chart directory")
        
        # Check if the directory exists
        if not system.dir_exists(dir_path):
            logger.debug(f"Directory {dir_path} does not exist")
            return False
        
        # Check for required files
        for file in required_files:
            file_path = system.join_paths(dir_path, file)
            if not system.file_exists(file_path):
                logger.debug(f"Required file {file_path} does not exist")
                return False
        
        # Check for required directories
        for dir in required_dirs:
            dir_path = system.join_paths(dir_path, dir)
            if not system.dir_exists(dir_path):
                logger.debug(f"Required dir {file_path} does not exist")
                return False
        
        return True

    def detectChangedReleases(self, repo_path: str, diffs: List[MergeRequestDiff]) -> List[str]:
        '''Detect if any of the changed files from the list of diffs are in a helm chart directory. Return a list of paths to changed helm charts'''
        changed_charts_paths = []
        for diff in diffs:
            old_path = system.join_paths(repo_path, diff.old_path) 
            new_path = system.join_paths(repo_path, diff.new_path)

            ## If multiple files are changed in the same chart and this path is a child of a chart path, skip it
            new_path_is_under_known_chart_path = any(changed_charts_path in new_path for changed_charts_path in changed_charts_paths)
            old_path_is_under_known_chart_path = any(changed_charts_path in old_path for changed_charts_path in changed_charts_paths)
            if  new_path_is_under_known_chart_path or old_path_is_under_known_chart_path:
                logger.info(f"Already detected changes detected in this chart path. Skipping...")
                continue
            
            ## Check the new file path
            if chart_root := self.fileIsInChartDirectory(file_path=new_path, root_dir=repo_path):
                changed_charts_paths.append(chart_root)
            else:
                logger.info(f"Modified Path {diff.new_path} is not in a helm chart directory")
            
            ## If the file has an old path that is diff from new_path, check if it was a helm chart directory
            if old_path != new_path:
                if chart_root := self.fileIsInChartDirectory(file_path=old_path, root_dir=repo_path):
                    changed_charts_paths.append(chart_root)
                else:
                    logger.info(f"Old Path {diff.old_path} is not in a helm chart directory")
        return changed_charts_paths


    def _ensureVersion(self) -> bool:
        # Check if Helm is already installed
        try:
            result = subprocess.run(['helm', 'version', '--template', '{{.Version}}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            logger.info("Helm bin could not be found")
            return None

        if result.returncode == 0:
            installed_version = result.stdout.decode('UTF-8').lower().lstrip('v').split('-')[0]
            logger.debug(f"Helm already installed at version: {installed_version}")
            return installed_version == self.version
        else:
            stdout = result.stdout.decode('UTF-8')
            stderr = result.stderr.decode('UTF-8')
            logger.info(f"Checking the version got failed exit code. STDOUT: {stdout}\nSTDERR: {stderr}")
            return False

    def _map_platforms(self, platform: machine_enum.Platform) -> enum.HelmPlatform:
        '''Map the generic platform enums to those for helm'''
        match platform:
            case machine_enum.Platform.DARWIN:
                return enum.HelmPlatform.DARWIN
            case machine_enum.Platform.LINUX:
                return enum.HelmPlatform.LINUX
            case machine_enum.Platform.WINDOWS:
                return enum.HelmPlatform.WINDOWS
            case _:
                raise ValueError(f"Unknown machine platform {platform} cannot be mapped to helm platforms")

    def _map_arch(self, arch: machine_enum.Arch) -> enum.HelmArch:
        '''Map generic arch enums to helm arch enums'''
        match arch:
            case machine_enum.Arch.AMD64:
                return enum.HelmArch.AMD64
            case machine_enum.Arch.ARM64:
                return enum.HelmArch.ARM64
            case _:
                raise ValueError(f"Unknown machine arch: {arch}")

    def _installVersion(self):
        if not self._ensureVersion():
            platform = self._map_platforms(system.getPlatform())
            arch = self._map_arch(system.getArch())
            helm_version = self.version

            # target files
            tarball_filename = f"helm-v{helm_version}-{platform}-{arch}.tar.gz"
            checksum_filename = f"{tarball_filename}.sha256sum"

            # Construct the download URLs
            helm_tarball_url = f"{Helm.BASE_INSTALL_URL}/{tarball_filename}"
            checksum_url = f"{Helm.BASE_INSTALL_URL}/{checksum_filename}"

            ## Download the Helm tarball and checksum
            logger.debug(f"Downloading Helm from {helm_tarball_url}")
            system.curl(args=['-LO'], url=helm_tarball_url)
            logger.debug(f"Downloading checksum from {checksum_url}")
            system.curl(args=['-LO'], url=checksum_url)

            system.validate_checksum(tarball_filename, checksum_filename)
         
            # Extract the tarball
            system.extract(tarball_filename)
            
            # Move the Helm binary to /usr/local/bin
            extracted_folder = f"{platform}-{arch}"
            extracted_bin = f"{extracted_folder}/helm"
            system.move_to_path(file=extracted_bin, path_dir=self.bin_path, bin_name="helm")

            # Clean up the tarball and extracted directory
            system.remove_file(tarball_filename)
            system.remove_file(checksum_filename)
            system.remove_dir(extracted_folder)

            if self._ensureVersion():
                logger.info("Helm installed successfully.")
            else:
                raise Exception("Helm installation failed with unknown failure")