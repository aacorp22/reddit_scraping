"""praw manipulator"""
from typing import Any
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


def base36_to_10(in_str: str) -> int:
    """https://www.reddit.com/r/pushshift/comments/11uc4cz/getting_comments_from_submission_id/"""
    return int(in_str, 36)


def make_recursive_requests(link: str, cooldown_timer: int, type_: str) -> str:
    """get request link and return json"""
    try:
        response = requests.get(link)
        if type_ == "posts":
            logging.info(f'\t\t\t\t\t[Response status code {type_}] {response.status_code}')
        data = response.json()
    except requests.RequestException:
        logging.error(f"Connection error in {link}, system will wait 30 sec")
        time.sleep(5)
        data = make_recursive_requests(link, cooldown_timer+5, type_)
    except JSONDecodeError:
        logging.info(f"Too many requests in {type_},"
                     f" system will wait {cooldown_timer} seconds"
                     " before the next request")
        time.sleep(cooldown_timer)
        data = make_recursive_requests(link, cooldown_timer+5, type_)
    return data


def make_recursive_for_author(link: str, cooldown_timer: int) -> Any:
    """get request link and return response"""
    try:
        response = requests.get(link)
    except requests.RequestException:
        logging.error(f"Connection error in get_author, system will wait 30 sec")
        time.sleep(5)
        response = make_recursive_for_author(link, cooldown_timer+5)

    try:
        response.json()
    except JSONDecodeError:
        logging.info("Too many requests in author_info,"
                     f" system will wait {cooldown_timer} seconds"
                     " before the next request")
        time.sleep(cooldown_timer)
        response = make_recursive_for_author(link, cooldown_timer+5)

    return response


def get_from_praw(id_: str, type_: str) -> dict:
    """func to make requests with praw api to get post, comment or author info

    Args:
        id_ (str): object id
        type_ (str): submission/author/comment

    Returns:
        dict: object data
    """
    info = {}
    try:
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
    except requests.RequestException:
        logging.error("Connection Error in get_from_praw, waiting for 6 seconds...")
        time.sleep(6)
        info = get_from_praw(id_, type_)

    return info


def get_comments(submission_id: str) -> None:
    """Function to parse all comments for a submission

    Args:
        submission_id (str): submission id
    """
    base = "https://api.pushshift.io/reddit/comment/search/?"
    data = pd.DataFrame()
    print("parsing comments")
    time.sleep(2)
    sub_id = base36_to_10(submission_id)
    while True:
        try:
            requests_link = f'{base}link_id={sub_id}&subreddit=wallstreetbets'
            response = make_recursive_requests(requests_link, 5, "comments")
            info = response["data"]
        except:
            logging.warning(f'[Post {submission_id}] {response}')
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
