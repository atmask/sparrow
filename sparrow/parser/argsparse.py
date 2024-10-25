import argparse
import shlex

from sparrow.parser.exceptions import ArgumentError


class SparrowCommandParser(argparse.ArgumentParser):

    def parse_from_str(self, command: str):
        '''Parse a command from a given input string by splitting it into a list of shell-like arguments'''
        return self.parse_args(shlex.split(command))
    
    def exit(self, status: int = 0, message: str | None = None):
        '''Override the exit method to raise an error instead of exiting the program'''
        self.error(message)
    
    def error(self, message: str):
        '''Override the error method to raise an error instead of exiting the program'''
        raise ArgumentError(message)

