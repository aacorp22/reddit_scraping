'''Main file to run functions and parse data'''
from src.parser import get_post_data


dataframe = get_post_data()
dataframe.to_excel('test.xlsx')
