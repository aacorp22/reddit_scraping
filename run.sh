rm -r env/
python3 -m venv env
source env/bin/activate
env/bin/python3 -m pip install -r requirements.txt
env/bin/python3 main.py
deactivate
