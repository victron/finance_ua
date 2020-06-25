import os
import logging
logger = logging.getLogger(__name__)

file_with_code = 'secret_data.pye'
stdinput = False

env_secret = "secret_berlox"
try:
    password = os.environ[env_secret]
except KeyError as key_err:
    logger.error(f"no environment {env_secret}")
    raise key_err
except Exception as e:
    logger.error(f"unknown error")
    raise e

