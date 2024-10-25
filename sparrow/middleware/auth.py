from sparrow.settings import BASIC_AUTH_ENABLED, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD
from werkzeug.wrappers import Request, Response, ResponseStream
from sparrow.logger import logger

'''Write a flask middleware that will require basic authentication for all routes'''
class BasicAuthMiddleware(object):
    def __init__(self, app):
        self.app = app
        self._enabled = BASIC_AUTH_ENABLED
        self._username = BASIC_AUTH_USERNAME
        self._password = BASIC_AUTH_PASSWORD

    def _get_auth_creds(self, request: Request):
        return request.authorization.username, request.authorization.password
    
    def _is_authenticated(self, username, password):
        return username == self._username and password == self._password

    def __call__(self, environ, start_response):

        ## If the Auth middleware is not enabled, just return the app
        if not self._enabled:
            logger.warning("Basic Auth is not enabled")
            return self.app(environ, start_response)

        # Get a request object
        request = Request(environ)
        username, password = self._get_auth_creds(request)

        # Pass the call to the app if the user is authenticated else return 401
        if self._is_authenticated(username, password):
            return self.app(environ, start_response)
        else:
            res = Response(u'Authorization failed', mimetype= 'text/plain', status=401)
            return res(environ, start_response)

        