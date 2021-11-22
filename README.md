# Reddit_scraping
Python script to make some data scraping for a research project

Script parses data from subreddit https://www.reddit.com/r/wallstreetbets

Dependencies are installed by

> pip install -r requirements.txt

After installing dependencies create *src/secrets.py* file
There you should provide your username, password, client id and client secret for the script to run correctly. Example of secrets.py file is in src folder, just put your own creds there and rename it.
To get client secret and client id, just go to https://www.reddit.com/prefs/apps and create your own app

Run

> python main.py

in your console, this will create an excel file, containing parsed data.
