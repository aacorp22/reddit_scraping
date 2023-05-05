'''file containing parsing functions'''
import time
import warnings
import logging
import pandas as pd
from pathlib import Path
from dateutil import parser as date_parser
from datetime import datetime
from prawcore.exceptions import NotFound

from src.praw_manipulator import make_recursive_for_author, get_comments,\
                                 make_recursive_requests, get_from_praw
from config.config_reader import read_config


warnings.simplefilter(action='ignore', category=FutureWarning)

logging.basicConfig(filename='application.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

CONFIG = read_config()


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
            'Title': submission['title'],
            'Body Text': submission['selftext'],
            'Author': post['author'],
            'Comments Number': submission['comments'],
            'Upvote Ratio': submission['upvote_ratio'],
            'Ups': submission['ups'],
            'Downs': submission['downs'],
            'Awards':submission['awards'],
            'Score': submission['score'],
            'Images': get_images_count(submission['selftext']),
            'Created': datetime.fromtimestamp(post['created_utc'])
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Edited': check_if_edited(submission['edited']),
            'Deleted': check_if_deleted(submission['selftext'], submission['title']),
            'Author Id': post['author_fullname'],
            'Author Total Submissions': author_info['all_submissions'],
            'Author Total Comments': author_info['all_comments'],
            'Author wallstreetbets submissions': author_info['wallstreet_submissions'],
            'Author wallstreetbets comments': author_info['wallstreet_comments'],
            'Author Account Created': datetime.fromtimestamp(author_created['account_created'])
                                    .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Link': post['url']
        }, ignore_index=True)
    except (KeyError, NotFound):
        df = df.append({}, ignore_index=True)

    return df


def check_if_edited(edited_var) -> str:
    """check if post has been edited, 1 = edited, 0 = not"""
    if edited_var is False:
        return "False"
    return "Edited"


def check_if_deleted(body: str, title: str) -> str:
    """check if post deleted or not"""
    text = f"{body} {title}"
    if "[removed]" in text or "[deleted]" in text:
        return "Deleted"
    return "False"


def get_author_info(author: str) -> int:
    """Function to get author's total comments or submissions number

    Args:
        author (str): author

    Returns:
        int: dictionary
    """
    info = {'all_comments': 0, 'all_submmissions': 0,
            'wallstreet_comments': 0, 'wallstreet_submissions': 0}

    base = 'https://api.pushshift.io/reddit/search/'
    comments_url = f'{base}comment/?author={author}&metadata=true&size=1'
    submission_url = f'{base}submission/?author={author}&metadata=true&size=1'
    wallstreet_comments = f'{base}comment/?author={author}&subreddit=wallstreetbets&metadata=true&size=1'
    wallstreet_submissions = f'{base}submission/?author={author}&subreddit=wallstreetbets&metadata=true&size=1'
    try:
        sub_request = make_recursive_for_author(submission_url, 5)
        info['all_submissions'] = sub_request.json()['metadata']['es']['hits']['total']['value']
        time.sleep(1.2)
        wallstreet_subm_request = make_recursive_for_author(wallstreet_submissions, 5)
        info['wallstreet_submissions'] = wallstreet_subm_request.json()['metadata']['es']['hits']['total']['value']
    except Exception as err:
        logging.warning(f'[Error decoding submissions in author info] {err}')
        time.sleep(2.2)

    try:
        com_request = make_recursive_for_author(comments_url, 5)
        info['all_comments'] = com_request.json()['metadata']['es']['hits']['total']['value']
        time.sleep(1.2)
        wallstreet_comm_request = make_recursive_for_author(wallstreet_comments, 5)
        info['wallstreet_comments'] = wallstreet_comm_request.json()['metadata']['es']['hits']['total']['value']
    except Exception as err:
        logging.warning(f'[Error decoding comments in author info] {err}')
        time.sleep(2.2)

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
        info.reset_index(drop=True, inplace=True)
        info.to_csv(file_path, header=True, mode='w', index=False)


def get_images_count(post_body: str) -> int:
    """Parse images count from post

    Args:
        post body selftext: post to parse

    Returns:
        int: number of images
    """
    images = post_body.count("https://preview.redd.it/")

    return images


def get_df_tail(filename: str, lines_number: int):
    """reads dataframe and returns last {lines_number} lines"""
    df = pd.read_csv(filename)

    return df.tail(lines_number).to_dict()


def get_all_data() -> pd.DataFrame:
    """Function to get posts from reddit,
        parse it and return a dataframe

    Returns:
        pd.DataFrame: parsed data in dataframe
    """
    base = "https://api.pushshift.io/reddit/search/submission/?"
    size = 500
    subreddit = 'wallstreetbets'
    if Path("submissions.csv").exists():
        last_row = get_df_tail("submissions.csv", 1)
        post_info = list(last_row["Created"].values())
        before_time_str = post_info[0]
        before_time_raw = date_parser.parse(before_time_str)
        before_time = str(before_time_raw.timestamp())[:-2]
        logging.info(f"Started parsing from last post's time: {before_time}")
    else:
        before_time = CONFIG["BEFORE_TIME"]
        logging.info(f"Started parsing from unix time: {before_time}")

    count = 1
    data = pd.DataFrame()
    comment_data = pd.DataFrame()
    comments_temp = pd.DataFrame()
    begin_time = datetime.now()
    work = True

    while work:
        request_url = f"{base}size={size}&subreddit={subreddit}&before={before_time}"
        response_data = make_recursive_requests(request_url, 5, "posts")

        if 'data' in response_data:
            info = response_data['data']
            logging.info(f'\t\t\t\t\t[Posts to work with: {len(info)}]')

            if len(info) == 0:
                logging.info(f'Finished parsing, posts left to parse: {len(info)}')
                logging.info(f"Total parsing time: {datetime.now() - begin_time}")
                break

            for post in info:
                if 'selftext' in post and\
                            'link_flair_text' in post and\
                            post['link_flair_text']=='DD' and\
                            post['selftext'] != '[removed]':
                    print(post['id'])

                    if post['created_utc'] < 1650965272:
                        print(post['created_utc'])
                        print("older posts coming")
                        count = 5
                        work = False
                        break
                    new_df = make_post_df(post)
                    time.sleep(0.2)
                    comments_temp =  get_comments(post['id'])

                    if not comments_temp.empty:
                        comment_data = comment_data.append(comments_temp,
                                                    ignore_index=True)

                    if not new_df.empty:
                        data = data.append(new_df, ignore_index=True)
                        logging.info(f'[Post {post["id"]}] Parsed')
                    else:
                        logging.info(f'[Post {post["id"]}] Partly parsed')

            count+=1
            if not count%15:
                data.drop_duplicates(subset=['Title'])
                data_to_csv(data, 'submissions.csv')
                logging.info(f'\t\t\t\t[Exported {len(data)} posts to csv]')
                data = pd.DataFrame()
                data_to_csv(comment_data, 'comments.csv')
                logging.info(f'\t\t\t\t[Exported {len(comment_data)} comments to csv]')
                comment_data = pd.DataFrame()
        else:
            last_time_from_dataframe = data.tail(1)['Created']
            logging.info(f'[Last retreived post`s date is {last_time_from_dataframe}]')
            logging.info(f"Total parsing time: {datetime.now() - begin_time}")
            logging.error(response_data)
            break

        before_time = info[-1]['created_utc']