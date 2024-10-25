from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from sparrow.cloudproviders.exceptions import AuthenticationError
from sparrow.logger import logger


def handle_auth_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientAuthenticationError as e:
            logger.exception(f"Failed to authenticate to Azure: {e}")
            raise AuthenticationError(f"Failed to authenticate to Azure. No credentials found.")
        except HttpResponseError as e:
            logger.exception(f"Failed to validate authorization on Azure: {e}")
            raise AuthenticationError(f"Insufficient permissions on Azure. Did you just add new privileges?")
        
        
    # Manually set the wrapper's attributes to match the original function
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


