from enum import StrEnum

class HelmPlatform(StrEnum):
    LINUX = 'linux'
    WINDOWS = 'windows'
    DARWIN = 'darwin'

class HelmArch(StrEnum):
    AMD64 = 'amd64'
    ARM64 = 'arm64'
