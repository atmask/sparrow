from .manager import LoggerManager
from enum import Enum
from .standard import StandardLogger

class LoggerType:
    STANDARD = 1

def LoggerFactory(name: str, logger_type: LoggerType):
    if logger := LoggerManager.getLogger(name):
        return logger
    else:
        match logger_type:
            case LoggerType.STANDARD:
                return LoggerManager.add(StandardLogger(name))
