'''file containing parsing functions'''
import time
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
    try:
        author_info = get_author_info(post['author'])
        submission = get_from_praw(post['id'], 'submission')
        author_created = get_from_praw(post['author_fullname'], 'author')
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
            'Images': get_images(post),
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
        time.sleep(5)
        try:
            info['submissions'] = sub_request.json()['metadata']['total_results']
        except JSONDecodeError:
            print(f'[Error decoding submissions in author info] {sub_request}')
    try:
        info['comments'] = com_request.json()['metadata']['total_results']
    except JSONDecodeError:
        time.sleep(5)
        try:
            info['comments'] = com_request.json()['metadata']['total_results']
        except JSONDecodeError:
            print(f'[Error decoding comments in author info] {com_request}')
    return info


def data_to_csv(info: pd.DataFrame, path: str) -> None:
    """Function to export dataframe to csv

    Args:
        info (pd.DataFrame): dataframe
        path (str): where to export
    """
    file_path = Path(path)
    if file_path.exists():
        info.to_csv(file_path, header=False, mode='a', index=False)
    else:
        info.to_csv(file_path, header=True, mode='w', index=False)


def get_images(post: dict) -> int:
    """Parse images from post

    Args:
        post (dict): post to parse

    Returns:
        int: number of images
    """
    images = 0
    if 'is_gallery' in post\
        and 'media_metadata' in post:
        images = len(post['media_metadata'])
    elif 'preview' in post and 'images' in post['preview']:
        images = len(post['preview']['images'])
    return images


def get_data() -> pd.DataFrame:
    """Function to get posts from reddit,
        parse it and return a dataframe

    Returns:
        pd.DataFrame: parsed data in dataframe
    """
    base = "https://api.pushshift.io/reddit/search/submission/?"
    size = 500
    subreddit = 'wallstreetbets'
    before_time = '1m'
    count = 1
    data = pd.DataFrame()
    comment_data = pd.DataFrame()
    comments_temp = pd.DataFrame()
    while(True):
        response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
        print(f'\t\t\t\t\t[Response status code] {response.status_code}')
        try:
            response.json()
        except JSONDecodeError:
            print(f'[INFO: Too many requests,\
                system will wait 5 seconds\
                before the next request]')
            time.sleep(5)
            try:
                response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
            except JSONDecodeError:
                print(f'[INFO: Too many requests,\
                    system will wait 10 seconds\
                    before the next request]')
                time.sleep(10)
                response = requests.get(f"{base}size={size}&subreddit={subreddit}&before={before_time}")
        if 'data' in response.json():
            info = response.json()['data']
            print(f'\t\t\t\t\t[Posts to work with: {len(info)}]')
            if len(info) == 0:
                print(f'Finished parsing, more posts found: {len(info)}')
                break

            for post in info:
                if 'selftext' in post and\
                    'link_flair_text' in post and\
                    post['link_flair_text']=='DD' and\
                    post['selftext'] != '[removed]':
                    new_df = make_post_df(post)
                    comments_temp =  get_comments(post['id'])
                    if not comments_temp.empty:
                        comment_data = comment_data.append(comments_temp,
                                                    ignore_index=True)
                    if not new_df.empty:
                        data = data.append(new_df, ignore_index=True)
                        print(f'[Post {post["id"]}] Parsed')
                    else:
                        print(f'[Post {post["id"]}] Partly parsed')

            count+=1
            if not count%10:
                data.drop_duplicates(subset=['Title'])
                data_to_csv(data, 'submissions.csv')
                print(f'\t\t\t\t[Exported {len(data)} posts to excel]')
                data = pd.DataFrame()
                data_to_csv(comment_data, 'comments.csv')
                print(f'\t\t\t\t[Exported {len(comment_data)} comments to excel]')
                comment_data = pd.DataFrame()
        else:
            last_time_from_dataframe = data.tail(1)['Created']
            with open('READ_ABOUT_ERROR_HERE.txt', 'w') as file:
                file.write(f'[Last retreived post`s date is {last_time_from_dataframe}]')
                file.write('\n')
                file.write(response.status())
            break

        before_time = info[-1]['created_utc']
