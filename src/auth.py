'''file for authorizing in reddit and getting auth token'''
import requests


def get_headers_with_token(id_: str,
              secret: str,
              username: str,
              password: str
              ) -> str:
    """Function to authorize in reddit and get auth token

    Args:
        id_ (str): CLIENT_ID
        secret (str): CLIENT_SECRET
        username (str): USERNAME
        password (str): PASSWORD

    Returns:
        str: token received
    """
    client_auth = requests.auth.HTTPBasicAuth(id_,secret)
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password
    }
    headers = {'User-Agent': 'myBot/0.0.1'}

    response = requests.post('https://www.reddit.com/api/v1/access_token',
                        auth=client_auth,
                        data=data,
                        headers=headers)
    TOKEN = f"bearer {response.json()['access_token']}"

    headers['Authorization'] = TOKEN
    return headers
