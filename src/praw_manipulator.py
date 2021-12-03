'''praw manipulator'''
import praw
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from json import JSONDecodeError
from src.secrets import CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD, USER_AGENT

reddit = praw.Reddit(
    user_agent=USER_AGENT,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    username=USERNAME,
    password=PASSWORD
)

def get_from_praw(id_: str, type_: str) -> int:
    """func to make requests with praw api to get post info

    Args:
        id_ (str): post id
        type_ (str): what field of post to get

    Returns:
        int: value
    """
    info = {}
    if type_ == 'submission':
        submission = reddit.submission(id_)
        try:
            info = {'comments': submission.num_comments,
                    'upvote_ratio': submission.upvote_ratio,
                    'ups': submission.ups,
                    'downs': submission.downs,
                    'awards': submission.total_awards_received,
                    'score': submission.score}
        except Exception as error:
            print(f'[Post {id_}] Could not get additional info {error}')
            info = {'comments': 0,
                    'upvote_ratio': 0.0,
                    'ups': 0,
                    'downs': 0,
                    'awards': 0,
                    'score': 0}
    elif type_ == 'author':
        try:
            user = reddit.redditor(fullname=id_)
            info['account_created'] = user.created_utc
        except Exception as error:
            print(f'[Author {id_}] Could not get account creation date {error}')
    return info


def get_comments(submission_id: str) -> None:
    """Function to parse all comments for a submission

    Args:
        submission_id (str): submission id
    """
    base = 'https://api.pushshift.io/reddit/comment/search/?'
    data = pd.DataFrame()
    while(True):
        response = requests.get(f"{base}link_id={submission_id}&subreddit=wallstreetbets")
        if response.status_code == 429:
            time.sleep(1)
        try:
            info = response.json()['data']
        except JSONDecodeError as err:
            print(f'[Post {submission_id}] {err} {response.status_code}')
            break

        if len(info) == 0:
            print(f'[Post {submission_id}] Does not have comments')
            break

        for post in info:
            try:
                if 'author' in post and\
                    post['author'] != '[deleted]' and\
                    post['body'] != '[deleted]' and\
                    not 'I am a bot' in post['body'] and\
                    not '**User Report**' in post['body']:
                    data = data.append({
                        'Comment Id':post['id'],
                        'Body': post['body'],
                        'Author':post['author'],
                        'Author Fullname':post['author_fullname'],
                        'Submission Id': submission_id,
                        'Created': datetime.fromtimestamp(post['created_utc'])
                                                .strftime('%Y-%m-%dT%H:%M:%SZ')},
                        ignore_index=True)
            except KeyError as error:
                print(f'[Post {post["id"]}] In get comments: {error}')
                pass

        if len(info) < 500:
            break

    file_path = Path('comments.csv')
    if file_path.exists():
        data.to_csv(file_path, header=False, mode='a', index=False)
    else:
        data.to_csv(file_path, header=True, mode='w', index=False)
    data = pd.DataFrame()
