'''Main file to run functions and parse data'''
from src.parser import get_data
from datetime import datetime

begin_time = datetime.now()

get_data()

print("\nScript total execution time:")
print(datetime.now() - begin_time)