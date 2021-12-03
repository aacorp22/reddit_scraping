'''file containing parsing functions'''
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from json import JSONDecodeError
from prawcore.exceptions import NotFound

from src.praw_manipulator import get_from_praw, get_comments


def make_post_df(post: dict) -> pd.DataFrame:
    """Func to parse data from dict

    Args:
        post (dict): dict to parse

    Returns:
        pd.DataFrame: parsed data in dataframe form
    """
    df = pd.DataFrame()
    author_info = get_author_info(post['author'])
    submission = get_from_praw(post['id'], 'submission')
    author_created = get_from_praw(post['author_fullname'], 'author')
    try:
        df = df.append({
            'Post Id': post['id'],
            'Flair Name': post['link_flair_text'],
            'Title': post['title'],
            'Body Text': post['selftext'],
            'Author': post['author'],
            'Comments Number': submission['comments'],
            'Upvote Ratio': submission['upvote_ratio'],
            'Ups': submission['ups'],
            'Downs': submission['downs'],
            'Awards':submission['awards'],
            'Score': submission['score'],
            'Created': datetime.fromtimestamp(post['created_utc'])
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Author Id': post['author_fullname'],
            'Author Total Submissions': author_info['submissions'],
            'Author Total Comments': author_info['comments'],
            'Author Account Created': datetime.fromtimestamp(author_created['account_created'])
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Link': post['url']
        }, ignore_index=True)
    except (KeyError, NotFound):
        df = df.append({}, ignore_index=True)
    return df


def get_author_info(author: str) -> int:
    """Function to get author's total comments or submissions number

    Args:
        author (str): author

    Returns:
        int: dictionary
    """
    info = {'comments': 0, 'submmissions': 0}
    base = 'https://api.pushshift.io/reddit/search/'
    comments_url = f'{base}comment/?author={author}&metadata=true&size=0'
    submission_url = f'{base}submission/?author={author}&metadata=true&size=0'
    sub_request = requests.get(submission_url)
    com_request = requests.get(comments_url)
    try:
        info['submissions'] = sub_request.json()['metadata']['total_results']
    except JSONDecodeError:
        print(f'[Error decoding submissions in author info] {sub_request}')

    try:
        info['comments'] = com_request.json()['metadata']['total_results']
    except JSONDecodeError:
        print(f'[Error decoding comments in author info] {com_request}')
    return info


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
    count = 1
    data = pd.DataFrame()
    while(count!=10):
        response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
        if 'data' in response.json():
            info = response.json()['data']
            if len(info) == 0 or count == 100:
                print(f'Finished parsing, posts before tha last found: {len(info)}')
                break

            for post in info:
                if 'selftext' in post and\
                    'link_flair_text' in post and\
                    post['link_flair_text']=='DD' and\
                    post['selftext'] != '[removed]':
                    new_df = make_post_df(post)
                    get_comments(post['id'])
                    if not new_df.empty:
                        data = data.append(new_df, ignore_index=True)
                        print(f'[Post {post["id"]}] Parsed')
                    else:
                        print(f'[Post {post["id"]}] Partly parsed')
                before_time = post['created_utc']

            count+=1
            if not count%1:
                file_path = Path('data.csv')
                if file_path.exists():
                    data.to_csv(file_path, header=False, mode='a', index=False)
                else:
                    data.to_csv(file_path, header=True, mode='w', index=False)
                data = pd.DataFrame()
        else:
            last_time_from_dataframe = data.tail(1)['Created']
            with open('READ_ABOUT_ERROR_HERE.txt', 'w') as file:
                file.write(f'[Last retreived post`s date is {last_time_from_dataframe}]')
                file.write('\n')
                file.write(response.status())
            break
