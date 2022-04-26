# Reddit_scraping
Python script to make some data scraping for a research project

Script parses data from subreddit https://www.reddit.com/r/wallstreetbets

Run script by shell command:

> source run.sh

System will cleate virtual environment, install required dependencies and run the script.

In *src/config/config.yml* you should provide your reddit username, password, client id and client secret for the script to run correctly. To get client secret and client id, just go to https://www.reddit.com/prefs/apps and create your own app.
More about authentication:
- https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps
- https://praw.readthedocs.io/en/stable/getting_started/authentication.html
