import requests

class AuthenticatedHTTPClient:
    '''
        A class that provides an interface for making authenticated requests and handling errors
    '''
    def __init__(self, auth_header: str, auth_token: str, base_url: str):
        self.auth_header = auth_header
        self.auth_token = auth_token
        self.base_url = base_url
        self._headers = {
            auth_header: auth_token
        }

    def post(self, path: str, headers: dict = {}, body: dict = {}):
        merged_headers = self._headers | headers
        return requests.post(url=f"{self.base_url}{path}", headers=merged_headers, data=body)

    def get(self, path: str, headers: dict = {}, body: dict = {}):
        merged_headers = self._headers | headers
        return requests.get(url=f"{self.base_url}{path}", headers=merged_headers, data=body)
