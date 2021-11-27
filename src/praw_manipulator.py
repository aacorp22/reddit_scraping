'''praw manipulator'''
import praw
import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
from src.secrets import CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD, USER_AGENT

reddit = praw.Reddit(
    user_agent=USER_AGENT,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    username=USERNAME,
    password=PASSWORD
)

def get_from_praw(id_: str, type_: str) -> int:
    """func to make requests with praw api to get post ups/downs

    Args:
        id_ (str): post id
        type_ (str): ups or downs

    Returns:
        int: value
    """
    submission = reddit.submission(id_)
    try:
        value = getattr(submission, type_)
    except Exception as error:
        print(error)
        value = 0
    return value


def get_comments(submission_id: str) -> None:
    """Function to parse all comments for a submission

    Args:
        submission_id (str): submission id
    """
    base = 'https://api.pushshift.io/reddit/comment/search/?'
    comment_ids = []
    data = pd.DataFrame()
    while(True):
        response = requests.get(f"{base}link_id={submission_id}&subreddit=wallstreetbets")
        info = response.json()['data']
        if len(info) == 0:
            print('No comments found')
            break

        for post in info:
            comment_ids.append(post['id'])
            try:
                data = data.append({
                    'Comment Id':post['id'],
                    'Body': post['body'],
                    'Author':post['author'],
                    'Author Fullname':post['author_fullname'],
                    'Created': datetime.fromtimestamp(post['created_utc'])
                                            .strftime('%Y-%m-%d')},
                    ignore_index=True)
            except KeyError as error:
                print(error)
                pass

        if len(info) < 500:
            break
    print(f'{submission_id} Comments retrieved: {str(len(info))}')
    file_path = Path('comments.csv')
    if file_path.exists():
        print('exists')
        data.to_csv(file_path, header=False, mode='a', index=False)
    else:
        print('not')
        data.to_csv(file_path, header=True, mode='w', index=False)
