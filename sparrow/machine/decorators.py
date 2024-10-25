
import subprocess

class SparrowSystemException(Exception):
    def __init__(self, message):
        super().__init__(message)

def handle_subprocess_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            raise SparrowSystemException(f"A called process error occurred: {e}. STDERR: {e.stderr}")
        except FileNotFoundError:
            raise SparrowSystemException(f"A File not found error occurred: {e}")
        except Exception as e:
            raise SparrowSystemException(f"An unexpected error occurred: {e}")
    
    # Manually set the wrapper's attributes to match the original function
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


