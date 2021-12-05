'''file to make excel format from csv'''
import pandas as pd

def make_excel() -> None:
    """Function to make excel from csv
    """
    comments = pd.read_csv('comments.csv')
    posts = pd.read_csv('submissions.csv')

    comments.to_excel('Comments.xlsx')
    posts.to_excel('Submissions.xlsx')
