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
    df = df.append({
        'Flair Name': post['data']['link_flair_text'],
        'Title': post['data']['title'],
        'Body Text': post['data']['selftext'],
        'Author': post['data']['author'],
        'Upvote Ratio': post['data']['upvote_ratio'],
        'Ups': post['data']['ups'],
        'Downs': post['data']['downs'],
        'Awards':post['data']['total_awards_received'],
        'Score': post['data']['score'],
        'Created (UTC)': datetime.fromtimestamp(post['data']['created_utc'])
                                .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'Author Fullname': post['data']['author_fullname'],
        'Link': post['data']['url'],
        'id': post['data']['id'],
        'kind': post['kind']
    }, ignore_index=True)
    return df


def get_data(headers: dict) -> pd.DataFrame:
    """Function to get data from reddit,
        parse it and return a dataframe

    Args:
        headers (dict): headers with token included

    Returns:
        pd.DataFrame: parsed data in dataframe
    """
    data = pd.DataFrame()
    params = {'limit': 100}

    for item in range(22):
        response = requests.get("https://oauth.reddit.com/r/wallstreetbets/",
                        headers=headers,
                        params=params)
        time.sleep(5)
        info = response.json()
        for post in info['data']['children']:
            if post['data']['link_flair_text']=='DD':
                new_df = df_from_response(post)
                data = data.append(new_df, ignore_index=True)
        print(len(data))
        last_row = data.iloc[len(data)-1]
        post_full_id = last_row['kind'] + '_' + last_row['id']
        params['after'] = post_full_id

    data = data.drop(columns=['id', 'kind'])
    return data
    #data.to_excel('data.xlsx')
