

class IHTTPClient:

    def __init__(self, auth_header :str , auth_token: str, base_url: str):
        ...

    def post(self, headers: str, body: str):
        ...

    def get(self, headers: str, body: str):
        ...