import logging

class StandardLogger:

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def basicConfig(self, *args, **kwargs):
        self._logger.basicConfig(*args, kwargs)

