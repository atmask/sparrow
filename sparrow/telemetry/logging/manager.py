from .interface import ILogger

class LoggerManager:
    _loggers = {}
    
    def getLogger(name: str) -> ILogger:
        return LoggerManager._loggers.get("name", None)
    
    def add(logger: ILogger) -> ILogger:
        LoggerManager._loggers[logger.name] = logger
        return logger
