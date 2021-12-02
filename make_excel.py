'''file to make excel format from csv'''
import pandas as pd

comments = pd.read_csv('comments.csv')
#posts = pd.read_csv('data.csv', error_bad_lines=False)

comments.to_excel('comments.xlsx')
#posts.to_excel('submissions.xlsx')
