import os

env_secret = "secret_berlox"
try:
    password = os.environ[env_secret]
except Exception as e:
    raise e
# file with secret functions
cleare_code = 'secret_data.py'
