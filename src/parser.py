'''file containing parsing functions'''
from pathlib import Path
import requests
import pandas as pd
from datetime import datetime
from src.praw_manipulator import get_from_praw, get_comments


def make_post_df(post: dict) -> pd.DataFrame:
    """Func to parse data from dict

    Args:
        post (dict): dict to parse

    Returns:
        pd.DataFrame: parsed data in dataframe form
    """
    df = pd.DataFrame()
    try:
        df = df.append({
            'Post Id': post['id'],
            'Flair Name': post['link_flair_text'],
            'Title': post['title'],
            'Body Text': post['selftext'],
            'Author': post['author'],
            'Comments Number': get_from_praw(post['id'], 'num_comments'),
            'Upvote Ratio': get_from_praw(post['id'], 'upvote_ratio'),
            'Ups': get_from_praw(post['id'], 'ups'),
            'Downs': get_from_praw(post['id'], 'downs'),
            'Awards':get_from_praw(post['id'], 'total_awards_received'),
            'Score': get_from_praw(post['id'], 'score'),
            'Created': datetime.fromtimestamp(post['created_utc'])
                                    .strftime('%Y-%m-%d'),
            'Author Id': post['author_fullname']
            #'Author Total Submissions': get_author_info(post['author_fullname'],'submissions')
            #'Author Total Comments': get_author_info(post['author_fullname'], 'comments')
            #'Link': post['url']
        }, ignore_index=True)
    except KeyError:
        df = df.append({'error':'1'}, ignore_index=True)
    return df


def get_author_info(fullname: str, type_: str) -> int:
    """Function to get author's total comments or submissions number

    Args:
        fullname (str): author's fullname
        type_ (str): comment or submission

    Returns:
        int: number
    """
    pass


def get_data() -> pd.DataFrame:
    """Function to get posts from reddit,
        parse it and return a dataframe

    Returns:
        pd.DataFrame: parsed data in dataframe
    """
    base = "https://api.pushshift.io/reddit/search/submission/?"
    size = 500
    subreddit = 'wallstreetbets'
    before_time = '1h'
    #count = 1
    data = pd.DataFrame()
    for i in range(3):
        response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
        info = response.json()['data']
        if len(info) == 0:
            print('No more posts found')
            break

        for post in info:
            if 'selftext' in post and\
                'link_flair_text' in post and\
                post['link_flair_text']=='DD' and\
                post['selftext'] != '[removed]':
                new_df = make_post_df(post)
                get_comments(post['id'])
                data = data.append(new_df, ignore_index=True)
            before_time = post['created_utc']

        #count+=1
        #if not count%10:
        file_path = Path('data.csv')
        if file_path.exists():
            data.to_csv(file_path, header=False, mode='a', index=False)
        else:
            data.to_csv(file_path, header=True, mode='w', index=False)
        data = pd.DataFrame()
        #count = 1