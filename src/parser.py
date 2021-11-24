'''file containing parsing functions'''
import time
import requests
import pandas as pd
from datetime import datetime


def df_from_response(post: dict) -> pd.DataFrame:
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
            'Comments Number': post['num_comments'],
            'Upvote Ratio': post['upvote_ratio'],
            #'Ups': post['ups'],
            #'Downs': post['downs'],
            'Awards':post['total_awards_received'],
            'Score': post['score'],
            'Created (UTC)': datetime.fromtimestamp(post['created_utc'])
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Author Id': post['author_fullname'],
            'Link': post['url']
        }, ignore_index=True)
    except KeyError:
        df = df.append({'error':'1'}, ignore_index=True)
    return df


def get_post_data() -> pd.DataFrame:
    """Function to get posts from reddit,
        parse it and return a dataframe

    Returns:
        pd.DataFrame: parsed data in dataframe
    """
    base = "https://api.pushshift.io/reddit/search/submission/?"
    data = pd.DataFrame()
    size = 500
    subreddit = 'wallstreetbets'
    before_time = '1h'
    for i in range(50):
        response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
        time.sleep(1)
        info = response.json()['data']
        if len(info) == 0:
            print('No more posts found')
            break

        for post in info:
            if 'selftext' in post and\
                post['link_flair_text']=='DD' and\
                post['selftext'] != '[removed]':
                new_df = df_from_response(post)
                data = data.append(new_df, ignore_index=True)
            before_time = post['created_utc']
        print(len(data))
    return data
