"""praw manipulator"""
import praw
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from json import JSONDecodeError

from config.config_reader import read_config


CONFIG = read_config()

reddit = praw.Reddit(
    user_agent=CONFIG["USER_AGENT"],
    client_id=CONFIG["CLIENT_ID"],
    client_secret=CONFIG["CLIENT_SECRET"],
    username=CONFIG["USERNAME"],
    password=CONFIG["PASSWORD"]
)


def get_from_praw(id_: str, type_: str) -> dict:
    """func to make requests with praw api to get post, comment or author info

    Args:
        id_ (str): object id
        type_ (str): submission/author/comment

    Returns:
        dict: object data
    """
    info = {}
    if type_ == "submission":
        try:
            submission = reddit.submission(id_)
            info = {"comments": submission.num_comments,
                    "upvote_ratio": submission.upvote_ratio,
                    "ups": submission.ups,
                    "downs": submission.downs,
                    "awards": submission.total_awards_received,
                    "score": submission.score,
                    "selftext": submission.selftext,
                    "edited": submission.edited,
                    "title": submission.title}
        except Exception as error:
            logging.warning(f'[Post {id_}] Could not get post info from praw {error}')
            info = {"comments": 0,
                    "upvote_ratio": 0.0,
                    "ups": 0,
                    "downs": 0,
                    "awards": 0,
                    "score": 0}
    elif type_ == "comment":
        try:
            comment = reddit.comment(id_)
            info = {"ups": comment.ups,
                    "downs": comment.downs,
                    "awards": comment.total_awards_received,
                    "score": comment.score,
                    "link": f"https://reddit.com{comment.permalink}"}
        except Exception as error:
            logging.warning(f'[Comment {id_}] Could not get comment data from praw {error}')
    elif type_ == "author":
        try:
            user = reddit.redditor(fullname=id_)
            info["account_created"] = user.created_utc
        except Exception as error:
            logging.warning(f'[Author {id_}] Could not get account creation date {error}')

    return info


def get_comments(submission_id: str) -> None:
    """Function to parse all comments for a submission

    Args:
        submission_id (str): submission id
    """
    base = "https://api.pushshift.io/reddit/comment/search/?"
    data = pd.DataFrame()
    while True:
        response = requests.get(f'{base}link_id={submission_id}&subreddit=wallstreetbets')
        try:
            info = response.json()["data"]
        except JSONDecodeError as err:
            time.sleep(5)
            try:
                info = response.json()["data"]
            except JSONDecodeError as err:
                logging.warning(f'[Post {submission_id}] {err} {response.status_code}')
                break

        if len(info) == 0:
            logging.info(f'[Post {submission_id}] Does not have comments')
            break

        for post in info:
            try:
                if "author" in post and\
                            post["author"] != "[deleted]" and\
                            post["body"] != "[deleted]" and\
                            not "I am a bot" in post["body"] and\
                            not "**User Report**" in post["body"]:
                    comment = get_from_praw(post["id"], "comment")
                    data = data.append({
                        "Comment Id":post["id"],
                        "Body": post["body"],
                        "Ups": comment["ups"],
                        "Downs": comment["downs"],
                        "Score": comment["score"],
                        "Awards": comment["awards"],
                        "Author":post["author"],
                        "Author Fullname":post["author_fullname"],
                        "Submission Id": submission_id,
                        "Created": datetime.fromtimestamp(post["created_utc"])
                                           .strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "Link": comment["link"]},
                        ignore_index=True)
            except KeyError as error:
                logging.warning(f'[Could not get comment {post["id"]}]: {error}')

        if len(info) < 500:
            break

    return data
