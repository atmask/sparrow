
from sparrow.machine import enum
from sparrow.machine.decorators import handle_subprocess_exceptions
from typing import List
import sys
import os
import subprocess
import hashlib
import shutil

def getPlatform() -> enum.Platform:
    platform = sys.platform

    if platform.startswith('linux'):
        return enum.Platform.LINUX
    elif platform == 'darwin':
        return enum.Platform.DARWIN
    elif platform == 'win32':
        return enum.Platform.WINDOWS
    else:
        raise ValueError(f"Unknown Platform: {platform}")

def getArch() -> enum.Arch:
    arch = os.uname().machine
    match arch:
        case 'x86_64':
            return enum.Arch.AMD64
        case 'aarch64':
            return enum.Arch.ARM64
        case _:
            raise ValueError(f"Unknown system architecture: {arch}")
        
@handle_subprocess_exceptions
def curl(args: List[str], url: str):
    cmd = ['curl'] + args + [url]
    subprocess.run(cmd, check=True)

def validate_checksum(download_file: str, checksum_file: str):
        ## Validate Checksum
        with open(checksum_file, 'r') as f:
            expected_checksum = f.read().split()[0]
        
        with open(download_file, 'rb') as f:
            file_data = f.read()
            calculated_checksum = hashlib.sha256(file_data).hexdigest()

        if calculated_checksum != expected_checksum:
            raise ValueError(f"Checksum validation failed! {expected_checksum} != {calculated_checksum}")

@handle_subprocess_exceptions
def extract(tarball_file: str):
    subprocess.run(['tar', '-zxvf', tarball_file], check=True)
    
@handle_subprocess_exceptions
def move_to_path(file: str, path_dir: str="/app/bin", bin_name=None):
    bin_name = bin_name if bin_name else file
    subprocess.run(['mv', file, f'{path_dir}/{bin_name}'], check=True)

def remove_file(target: str):
    os.remove(target)

def remove_dir(target: str):
    shutil.rmtree(target)

def dir_exists(target: str) -> bool:
    return os.path.isdir(target)

def file_exists(target: str) -> bool:
    return os.path.isfile(target)

def join_paths(*args) -> str:
    return os.path.join(*args)

def get_parent_dir(target: str) -> str:
    return os.path.dirname(target)

def is_in_path(path: str) -> bool:
    system_path = os.environ.get('PATH')
    return path in system_path.split(os.pathsep)

def add_to_path(directory):
    if os.path.isdir(directory):
        os.environ["PATH"] = directory + os.pathsep + os.environ["PATH"] # Give top precendence
    else:
        raise Exception(f"{directory} is not a valid directory.")

def get_env_var(name: str) -> str:
    return os.environ.get(name, "")

def set_env_var(name: str, value: str):
    os.environ[name] = value

def unset_env_var(name: str):
    os.environ.pop(name)

def path_match_length(path1: str, path2: str) -> int:
    """Calculate the length of the shared path prefix between two paths"""
    min_length = min(len(path1), len(path2))
    for i in range(min_length):
        if path1[i] != path2[i]:
            return i
    return min_length

def create_dir(directory: str): 
    os.makedirs(directory, exist_ok=True)


def set_file_permissions(file: str, mode: int):
    os.chmod(file, mode)