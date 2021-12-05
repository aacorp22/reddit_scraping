'''Main file to run functions and parse data'''
from datetime import datetime
from src.make_excel import make_excel
from src.parser import get_data

begin_time = datetime.now()

get_data()
make_excel()

print("\nScript total execution time:")
print(datetime.now() - begin_time)
