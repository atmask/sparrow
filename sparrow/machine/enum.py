from enum import Enum

class Platform(Enum):
    LINUX = 0
    DARWIN = 1
    WINDOWS = 3

class Arch(Enum):
    AMD64 = 0
    ARM64 = 1