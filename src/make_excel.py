'''file to make excel format from csv'''
import logging
import pandas as pd

def make_excel() -> None:
    """Function to make excel from csv
    """
    try:
        logging.info("Formatting csv to xlsx...")
        # comments = pd.read_csv('comments.csv')
        posts = pd.read_csv('submissions.csv')

        # comments.to_excel('comments.xlsx')
        posts.to_excel('submissions.xlsx')
        logging.info("Format to excel succeded!")
    except FileNotFoundError:
        logging.error("Could not find csv files to convert to xlsx. Check filenames!")
