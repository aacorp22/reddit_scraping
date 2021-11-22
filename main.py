'''Main file to run functions and parse data'''
from src.auth import get_headers_with_token
from src.parser import get_data

from src.secrets import CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD

headers = get_headers_with_token(CLIENT_ID,
                                 CLIENT_SECRET,
                                 USERNAME,
                                 PASSWORD)
dataframe = get_data(headers)
dataframe.to_excel('data.xlsx')
